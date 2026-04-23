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
    """Generate a RAG-grounded reply.

    Retrieves the `top_k` most similar support tickets, then passes them as
    context to the LLM to generate a grounded reply. The response includes the
    retrieved sources so you can inspect what the model was shown.
    """
    t0 = time.time()
    retrieve_result = retrieve(request.text, request.top_k)
    user_prompt = build_rag_user_prompt(request.text, retrieve_result.sources)
    response = llm.call(user_prompt, GENERATE_RAG_PROMPT)
    latency_ms = (time.time() - t0) * 1000
    return RagGenerateResponse(
        response=response,
        latency_ms=latency_ms,
        cost_usd=0.0,
        retrieve=retrieve_result,
    )


@router.post("/no-rag", response_model=LLMResult)
async def generate_no_rag(request: QueryRequest):
    """Generate a reply without retrieval.

    Passes the query directly to the LLM with no retrieved context. Useful as
    a baseline to compare against the RAG endpoint.
    """
    t0 = time.time()
    response = llm.call(request.text, GENERATE_NO_RAG_PROMPT)
    latency_ms = (time.time() - t0) * 1000
    return LLMResult(response=response, latency_ms=latency_ms, cost_usd=0.0)
