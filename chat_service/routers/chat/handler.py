from fastapi import APIRouter, HTTPException
from openai import OpenAI
import logging
import os

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/c/{chat_item}")
async def handle_chat(chat_item: str):
    client = OpenAI(
        base_url=os.getenv("OPENAI_BASE_URL", "http://localhost:1234/v1"),  # Make sure `/v1` is included
        api_key=os.getenv("OPENAI_API_KEY", "lm-studio")  # Example: use env var; ensure 'os' is imported
    )
    try: 
        response = client.chat.completions.create(
            model="qwen2.5-0.5b-instruct",
            messages=[{"role": "user", 
                       "content": chat_item}]
        )
    except Exception as e:
        logger.error(f"Error during chat completion: {e}")
        raise HTTPException(status_code=500, detail="An internal server error occurred while processing your request.")
    

    return {"response": response.choices[0].message.content}
