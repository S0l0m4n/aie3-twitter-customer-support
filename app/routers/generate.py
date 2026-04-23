import time

from fastapi import APIRouter

import app.llm as llm
import app.retrieval as retrieval
from app.prompts.generate import (
    GENERATE_NO_RAG_PROMPT,
    GENERATE_RAG_PROMPT,
    build_no_rag_user_prompt,
    build_rag_user_prompt,
)
from app.schemas import QueryRequest, RagGenerateResponse, NoRagGenerateResponse

router = APIRouter(prefix="/generate", tags=["Debug"])


@router.post("/rag", response_model=RagGenerateResponse)
async def generate_rag(request: QueryRequest):
    t0 = time.time()
    sources = retrieval.retrieve(request.text, request.top_k)
    user_prompt = build_rag_user_prompt(request.text, sources)
    response = llm.call(user_prompt, GENERATE_RAG_PROMPT)
    latency_ms = (time.time() - t0) * 1000
    return RagGenerateResponse(response=response, sources=sources, latency_ms=latency_ms, cost_usd=0.0)


@router.post("/no-rag", response_model=NoRagGenerateResponse)
async def generate_no_rag(request: QueryRequest):
    t0 = time.time()
    response = llm.call(build_no_rag_user_prompt(request.text), GENERATE_NO_RAG_PROMPT)
    latency_ms = (time.time() - t0) * 1000
    return NoRagGenerateResponse(response=response, latency_ms=latency_ms, cost_usd=0.0)