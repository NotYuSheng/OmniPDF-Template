from fastapi import APIRouter, Body
from models.translate import TranslateResponse, DoclingTranslationResponse
# from typing import Optional

import logging
import requests

router = APIRouter(prefix="/translate", tags=["translate"])
logger = logging.getLogger(__name__)

# LLM_URL = "http://192.168.1.108:80/v1/chat/completions"
LLM_URL = "http://192.168.1.224:80/v1/chat/completions"
TOKEN = "token-abc123"

def translate(prompt, source_lang=None, target_lang="English"):
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

    r = requests.post(
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

    return r.json()["choices"][0]["message"]["content"]

@router.post("/translate", response_model=TranslateResponse)
def doc_translate(payload: TranslateResponse = Body(...)):
    doc_id = payload.doc_id
    data = payload.docling
    source_lang = payload.source_lang
    target_lang = payload.target_lang or "English"

    for i, entry in enumerate(data.texts):
        original_text = entry.get("text") or entry.get("orig")
        if original_text:
            translated_text = translate(original_text, source_lang=source_lang, target_lang=target_lang)
            entry_dict = dict(entry) if not isinstance(entry, dict) else entry
            entry_dict["trans"] = translated_text
            data.texts[i] = entry_dict  # update the list


    for table in data.tables:
        table_data = table.get("data", {})
        table_cells = table_data.get("table_cells", [])
        for i, entry in enumerate(table_cells):
            original_text = entry.get("text")
            if original_text:
                translated_text = translate(original_text, source_lang=source_lang, target_lang=target_lang)
                entry_dict = dict(entry) if not isinstance(entry, dict) else entry
                entry_dict["trans"] = translated_text
                table_cells[i] = entry_dict

    if source_lang:
        return TranslateResponse(
            doc_id = doc_id,
            source_lang = source_lang,
            target_lang = target_lang,
            docling = data
        )
    else:
        return TranslateResponse(
            doc_id = doc_id,
            target_lang = target_lang,
            docling = data
        )
