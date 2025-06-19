import logging

from fastapi import HTTPException
import httpx

logger = logging.getLogger(__name__)

# async def get_from_url():
#     async with httpx.AsyncClient() as client:
#         req = await client.get(getenv("IMAGE_PROCESSOR_URL") + f"/{doc_id}")

#         response.status_code = req.status_code
#         return req.content
    
async def proxy_get(url: str):
    async with httpx.AsyncClient() as client:
        try:
            req = await client.get(url)
            req.raise_for_status() # Raise an exception for bad status codes
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving from {url}: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Processor error: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error retrieving from {url}: {e}")
            raise HTTPException(status_code=500, detail=f"Could not connect to processor service: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in HTTP request {url}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error") from e
        return req
    
async def proxy_post(url: str, body: dict):
    async with httpx.AsyncClient() as client:
        try:
            req = await client.post(url, data=body)
            req.raise_for_status() # Raise an exception for bad status codes
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error retrieving from {url}: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=f"Processor error: {e.response.text}") from e
        except httpx.RequestError as e:
            logger.error(f"Request error retrieving from {url}: {e}")
            raise HTTPException(status_code=500, detail=f"Could not connect to processor service: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error in HTTP request {url}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Internal server error") from e
        return req