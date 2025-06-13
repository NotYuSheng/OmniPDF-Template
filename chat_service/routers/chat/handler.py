from fastapi import APIRouter, HTTPException, Depends
from openai import OpenAI, APIError
from client import get_openai_client
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{chat_item}")
async def handle_chat(chat_item: str, client: OpenAI = Depends(get_openai_client)):
    try: 
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "qwen2.5-0.5b-instruct"),
            messages=[{"role": "user", 
                       "content": chat_item}]
        )
    except APIError as e:
        logger.error(f"OpenAI API error: {e}")
        raise HTTPException(status_code=500, detail=f"AI service error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your request.")

    return {"response": response.choices[0].message.content}
