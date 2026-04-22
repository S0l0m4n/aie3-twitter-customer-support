import time

from fastapi import APIRouter
from app.schemas import QueryRequest, RetrieveResponse, Source

router = APIRouter(tags=["Debug"])


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: QueryRequest):
    t0 = time.time()
    # TODO: embed request.text, query ChromaDB, return Source objects
    sources: list[Source] = []
    latency_ms = (time.time() - t0) * 1000
    return RetrieveResponse(sources=sources, latency_ms=latency_ms)