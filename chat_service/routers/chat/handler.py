from fastapi import APIRouter, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from openai import OpenAI, APIError
from client import get_openai_client
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{chat_item}")
async def handle_chat(chat_item: str, client: OpenAI = Depends(get_openai_client)):
    try:
        response = await run_in_threadpool(
            client.chat.completions.create,
            model=os.getenv("OPENAI_MODEL", "qwen2.5-0.5b-instruct"),
            messages=[{"role": "user", "content": chat_item}],
        )
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred while communicating with the AI service.",
        )
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(
            status_code=500,
            detail="An internal server error occurred while processing your request.",
        )

    # Validate the response structure before accessing content
    if not response.choices or len(response.choices) == 0:
        logger.error("No choices found in OpenAI response: %s", response)
        raise HTTPException(
            status_code=500,
            detail="AI service returned no choices or an unexpected response format.",
        )

    first_choice = response.choices[0]
    if not first_choice.message or first_choice.message.content is None:
        logger.error(
            "No message or content in OpenAI response's first choice: %s", first_choice
        )
        raise HTTPException(
            status_code=500,
            detail="AI service response choice is malformed or lacks content.",
        )

    return {"response": first_choice.message.content}
