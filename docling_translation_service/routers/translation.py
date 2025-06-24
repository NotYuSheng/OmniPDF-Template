from fastapi import APIRouter, Query, Body
from models.translate import TranslateResponse, DoclingTranslationResponse
from typing import Optional

import logging
import requests

router = APIRouter(prefix="/translation", tags=["translation"])
logger = logging.getLogger(__name__)

# LLM_URL = "http://192.168.1.108:80/v1/chat/completions"
LLM_URL = "http://192.168.1.197:80/v1/chat/completions"
TOKEN = "token-abc123"

def translate(prompt, input_lang=None, output_lang="English"):
    if input_lang:
        system_prompt = (
            f"You are a professional translator. Given the input language '{input_lang}', "
            f"think deeply and translate the following to '{output_lang}'. "
            f"Return only the translated text."
        )
    else:
        system_prompt = (
            f"You are a professional translator. Think deeply and translate the following to '{output_lang}'. "
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

@router.post("/extract", response_model=TranslateResponse)
def doc_translate(
    data: DoclingTranslationResponse = Body(...),
    input_lang: Optional[str] = Query(None),
    output_lang: str = Query("English")
):
    for entry in data.texts:
        original_text = entry.get("text") or entry.get("orig")
        if original_text:
            translated_text = translate(original_text, input_lang=input_lang, output_lang=output_lang)
            entry["trans"] = translated_text

    for table in data.tables:
        table_data = table.get("data", {})
        table_cells = table_data.get("table_cells", [])
        for entry in table_cells:
            original_text = entry.get("text")
            if original_text:
                translated_text = translate(original_text, input_lang=input_lang, output_lang=output_lang)
                entry["trans"] = translated_text

    return TranslateResponse(
        doc_id=data.name,
        status="success",
        result=data
    )