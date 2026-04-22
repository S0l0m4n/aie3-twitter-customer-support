import time
from app.schemas import LLMResult, LLMPredictPriorityResponse, Source


async def generate_rag(query: str, sources: list[Source]) -> LLMResult:
    """Call Groq with RAG context. Returns LLMResult."""
    t0 = time.time()
    # TODO: build prompt, call Groq, parse response, calculate cost
    latency_ms = (time.time() - t0) * 1000
    return LLMResult(response="", latency_ms=latency_ms, cost_usd=0.0)


async def generate_no_rag(query: str) -> LLMResult:
    """Call Groq without context. Returns LLMResult."""
    t0 = time.time()
    # TODO: build prompt, call Groq, parse response, calculate cost
    latency_ms = (time.time() - t0) * 1000
    return LLMResult(response="", latency_ms=latency_ms, cost_usd=0.0)


async def predict_priority(query: str) -> LLMPredictPriorityResponse:
    """Zero-shot priority classification via Groq structured output."""
    t0 = time.time()
    # TODO: call Groq with json_schema strict mode, parse label + confidence
    latency_ms = (time.time() - t0) * 1000
    return LLMPredictPriorityResponse(label="normal", confidence=0.0, latency_ms=latency_ms, cost_usd=0.0)
