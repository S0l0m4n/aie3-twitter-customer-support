import time

from fastapi import APIRouter
from app.schemas import QueryRequest, RetrieveResponse
from app import retrieval

router = APIRouter(tags=["Debug"])


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: QueryRequest):
    t0 = time.time()
    sources = retrieval.retrieve(request.text, request.top_k)
    latency_ms = (time.time() - t0) * 1000
    return RetrieveResponse(sources=sources, latency_ms=latency_ms)