from fastapi import APIRouter
from app.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    raise NotImplementedError