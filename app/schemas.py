from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=3)


class PredictPriorityRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class Source(BaseModel):
    ticket_id: str
    customer_text: str
    brand_reply: str
    similarity: float


class RagGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    sources: list[Source]


class LLMResult(BaseModel):
    response: str
    latency_ms: float
    cost_usd: float


class MLPredictPriorityResponse(BaseModel):
    label: str
    confidence: float
    latency_ms: float
    cost_usd: float = 0.0


class LLMPredictPriorityResponse(BaseModel):
    label: str
    confidence: float
    latency_ms: float
    cost_usd: float


class QueryResponse(BaseModel):
    query: str
    sources: list[Source]
    rag_answer: LLMResult
    no_rag_answer: LLMResult
    ml_prediction: MLPredictPriorityResponse
    llm_prediction: LLMPredictPriorityResponse


class RetrieveResponse(BaseModel):
    sources: list[Source]
    latency_ms: float


class RagGenerateResponse(BaseModel):
    response: str
    sources: list[Source]
    latency_ms: float
    cost_usd: float


class NoRagGenerateResponse(BaseModel):
    response: str
    latency_ms: float
    cost_usd: float


class ErrorResponse(BaseModel):
    error: str
    status_code: int