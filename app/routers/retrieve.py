from fastapi import APIRouter
from app.schemas import QueryRequest, RetrieveResponse
from app.rag.retrieve import retrieve

router = APIRouter(tags=["Debug"])


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_sources(request: QueryRequest):
    return retrieve(request.text, request.top_k)
