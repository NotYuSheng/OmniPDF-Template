from fastapi import APIRouter, HTTPException
from openai import OpenAI
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/c/{chat_item}")
async def handle_chat(chat_item: str):
    client = OpenAI(
        base_url="http://localhost:1234/v1",  # Make sure `/v1` is included
        api_key="lm-studio"  # any dummy string
    )
    try: 
        response = client.chat.completions.create(
            model="qwen2.5-0.5b-instruct",
            messages=[{"role": "user", 
                       "content": chat_item}]
        )
    except Exception as e:
        logger.error(f"Error during chat completion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error: {e}")
    

    return {"response": response.choices[0].message.content}
