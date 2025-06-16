from fastapi import APIRouter

router = APIRouter()


@router.get("/status/{doc_id}")
async def embedding_check(doc_id: str):
    return {"status": f"{doc_id} embedded"}
