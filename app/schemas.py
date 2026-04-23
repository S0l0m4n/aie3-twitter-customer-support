from pydantic import BaseModel, Field
from typing import Literal


class QueryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=3)


class PredictPriorityResponse(BaseModel):
    label: Literal["normal", "urgent"]
    accuracy: float = Field(
        default=-1,
        description="Pre-computed accuracy of the response (-1 if missing)"
    )
    latency_ms: float
    cost_usd: float = 0.0


class Source(BaseModel):
    ticket_id: str
    customer_text: str
    brand_reply: str
    similarity: float


class LLMResult(BaseModel):
    response: str
    latency_ms: float
    cost_usd: float


class QueryResponse(BaseModel):
    query: str
    sources: list[Source]
    rag_answer: LLMResult
    no_rag_answer: LLMResult
    ml_prediction: PredictPriorityResponse
    llm_prediction: PredictPriorityResponse


class RetrieveResponse(BaseModel):
    sources: list[Source]
    latency_ms: float


class RagGenerateResponse(BaseModel):
    response: str
    sources: list[Source]
    latency_ms: float
    cost_usd: float = 0.0


class NoRagGenerateResponse(BaseModel):
    response: str
    latency_ms: float
    cost_usd: float = 0.0


class ErrorResponse(BaseModel):
    error: str
    status_code: int
