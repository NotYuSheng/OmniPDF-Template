from fastapi import Response, HTTPException
import httpx
import logging

logger = logging.getLogger(__name__)


async def proxy_request(url: str, response: Response):
    async with httpx.AsyncClient() as client:
        try:
            req = await client.get(url)
        except httpx.RequestError as e:
            logger.error(f"Request error retrieving from {url}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Could not connect to processor service: {e}"
            ) from e
        except Exception as e:
            logger.error(
                f"Unexpected error retrieving from {url}: {e}", exc_info=True
            )
            raise HTTPException(status_code=500, detail="Internal server error") from e
        response.status_code = req.status_code
        return req.content
