from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI, APIError
from .client import get_openai_client
import logging
import os
from models.chat import ChatRequest

router = APIRouter(prefix="/chat")
logger = logging.getLogger(__name__)


@router.post("/", status_code=201)
async def handle_chat(
    chat_request: ChatRequest,
    client: OpenAI = Depends(get_openai_client),
) -> dict[str, str]:
    try:
        response = await run_in_threadpool(
            client.chat.completions.create,
            model=os.getenv("OPENAI_MODEL", "qwen2.5-0.5b-instruct"),
            messages=[
                {
                    "role": "user",
                    "content": chat_request.message,
                    "doc_id": chat_request.doc_id
                    if hasattr(chat_request, "doc_id")
                    else None,
                }
            ],
        )
    except APIError:
        logger.exception("OpenAI API error:")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while communicating with the AI service.",
        )
    except Exception:
        logger.exception("An unexpected error occurred:")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing your request.",
        )

    if not response.choices:
        logger.error("No choices found in OpenAI response: %s", response)
        raise HTTPException(
            status_code=500,
            detail="AI service returned no choices or an unexpected response format.",
        )

    first_choice = response.choices[0]
    if not first_choice.message or first_choice.message.content is None:
        logger.error("Malformed choice in OpenAI response: %s", first_choice)
        raise HTTPException(
            status_code=500,
            detail="AI service response choice is malformed or lacks content.",
        )

    return {"response": first_choice.message.content}
