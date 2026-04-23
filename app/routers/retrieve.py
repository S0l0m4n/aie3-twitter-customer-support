from fastapi import APIRouter
from app.schemas import QueryRequest, RetrieveResponse
from app import retrieval

router = APIRouter(tags=["Debug"])


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: QueryRequest):
    sources = retrieval.retrieve(request.text, request.top_k)
    return RetrieveResponse(sources=sources)