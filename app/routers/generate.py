import time

from fastapi import APIRouter

import app.llm as llm
from app.rag.retrieve import retrieve
from app.prompts.generate import (
    GENERATE_NO_RAG_PROMPT,
    GENERATE_RAG_PROMPT,
    build_rag_user_prompt,
)
from app.schemas import LLMResult, QueryRequest, RagGenerateResponse

router = APIRouter(prefix="/generate", tags=["Debug"])


@router.post("/rag", response_model=RagGenerateResponse)
async def generate_rag(request: QueryRequest):
    t0 = time.time()
    sources = retrieve(request.text, request.top_k)
    user_prompt = build_rag_user_prompt(request.text, sources)
    response = llm.call(user_prompt, GENERATE_RAG_PROMPT)
    latency_ms = (time.time() - t0) * 1000
    return RagGenerateResponse(response=response, sources=sources, latency_ms=latency_ms, cost_usd=0.0)


@router.post("/no-rag", response_model=LLMResult)
async def generate_no_rag(request: QueryRequest):
    t0 = time.time()
    response = llm.call(request.text, GENERATE_NO_RAG_PROMPT)
    latency_ms = (time.time() - t0) * 1000
    return LLMResult(response=response, latency_ms=latency_ms, cost_usd=0.0)
