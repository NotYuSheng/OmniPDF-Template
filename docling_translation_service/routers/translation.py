from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse
from models.translate import TranslateResponse
from shared_utils.s3_utils import save_job, load_job

import os
import logging
import httpx  # Replaces requests for async calls

import asyncio
from asyncio import Semaphore
import traceback
import json

router = APIRouter(prefix="/translation", tags=["translation"])
logger = logging.getLogger(__name__)

LLM_URL = "http://qwen2.5:8000/v1/chat/completions"
TOKEN = os.getenv("LLM_API_TOKEN")

semaphore = Semaphore(5)

async def translate(prompt, source_lang=None, target_lang="English"):
    if source_lang:
        system_prompt = (
            f"You are a professional translator. Given the input language '{source_lang}', "
            f"think deeply and translate the following to '{target_lang}'. "
            f"Return only the translated text."
        )
    else:
        system_prompt = (
            f"You are a professional translator. Think deeply and translate the following to '{target_lang}'. "
            f"Detect the source language automatically and return only the translated text."
        )

    async with httpx.AsyncClient() as client:
        r = await client.post(
            LLM_URL,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TOKEN}"
            },
            json={
                "model": "qwen2.5",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0
            }
        )

    r.raise_for_status()
    try:
        response_json = r.json()
        return response_json["choices"][0]["message"]["content"]
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Failed to parse LLM response: {e}")
        return "[Translation Error]"

async def safe_translate(entry, source_lang, target_lang):
    async with semaphore:
        original_text = entry.get("text") or entry.get("orig")
        if original_text:
            translated = await translate(original_text, source_lang=source_lang, target_lang=target_lang)
            entry_dict = dict(entry) if not isinstance(entry, dict) else entry
            entry_dict["translated_text"] = translated
            return entry_dict
        return entry


@router.post("/", response_model=TranslateResponse)
async def doc_translate(payload: TranslateResponse = Body(...)):
    doc_id = payload.doc_id
    data = payload.docling
    source_lang = payload.source_lang
    target_lang = payload.target_lang or "English"

    logger.info(f"Received translation request: doc_id={doc_id}")
    save_job(doc_id=doc_id, job_data={}, status="processing", job_type="translation")

    # try:
    #     for i, entry in enumerate(data.texts):
    #         original_text = entry.get("text") or entry.get("orig")
    #         if original_text:
    #             translated_text = await translate(original_text, source_lang=source_lang, target_lang=target_lang)
    #             entry_dict = dict(entry) if not isinstance(entry, dict) else entry
    #             entry_dict["translated_text"] = translated_text
    #             data.texts[i] = entry_dict

    #     for table in data.tables:
    #         table_data = table.get("data", {})
    #         table_cells = table_data.get("table_cells", [])
    #         for i, entry in enumerate(table_cells):
    #             original_text = entry.get("text")
    #             if original_text:
    #                 translated_text = await translate(original_text, source_lang=source_lang, target_lang=target_lang)
    #                 entry_dict = dict(entry) if not isinstance(entry, dict) else entry
    #                 entry_dict["translated_text"] = translated_text
    #                 table_cells[i] = entry_dict

    #     save_job(doc_id=doc_id, job_data=data, status="completed", job_type="translation")
    #     logger.info(f"Translation completed: doc_id={doc_id}")

    #     return TranslateResponse(
    #         doc_id=doc_id,
    #         source_lang=source_lang,
    #         target_lang=target_lang,
    #         docling=data
    #     )
    # except Exception as e:
    #     logger.error(f"Translation failed: doc_id={doc_id} - {e}")
    #     save_job(doc_id=doc_id, job_data={}, status="failed", job_type="translation")
    #     return JSONResponse(content={"error": "Translation failed."}, status_code=500)
    try:
        # Translate texts concurrently
        text_tasks = [
            safe_translate(entry, source_lang, target_lang)
            for entry in data.texts
        ]
        data.texts = await asyncio.gather(*text_tasks)

        # Translate table_cells concurrently
        for table in data.tables:
            table_data = table.get("data", {})
            table_cells = table_data.get("table_cells", [])
            table_tasks = [
                safe_translate(entry, source_lang, target_lang)
                for entry in table_cells
            ]
            table_data["table_cells"] = await asyncio.gather(*table_tasks)

        save_job(doc_id=doc_id, job_data=data, status="completed", job_type="translation")
        logger.info(f"Translation completed: doc_id={doc_id}")

        return TranslateResponse(
            doc_id=doc_id,
            source_lang=source_lang,
            target_lang=target_lang,
            docling=data
        )
    except Exception as e:
        logger.error(f"Translation failed: doc_id={doc_id} - {e}")
        logger.error(traceback.format_exc())
        save_job(doc_id=doc_id, job_data={}, status="failed", job_type="translation")
        return JSONResponse(content={"error": "Translation failed."}, status_code=500)


@router.get("/status/{doc_id}")
def get_status(doc_id: str):
    job = load_job(doc_id=doc_id, job_type="translation")
    if job is None:
        return JSONResponse(content="failed", status_code=404)

    return JSONResponse(
        content=job["status"],
        status_code=200 if job["status"] == "completed" else 202
    )
