from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Returns the operational status of the FastAPI server"""

    return {"status": "ok"}
