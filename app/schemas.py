from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Literal


class QueryRequest(BaseModel):
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "text": "My order hasn't arrived and it's been two weeks. This is completely unacceptable!",
            "top_k": 3,
        }
    })

    text: str = Field(..., min_length=1, max_length=1000)
    top_k: int = Field(default=3)


class PredictPriorityResponse(BaseModel):
    label: Literal["normal", "urgent"]
    confidence: float = Field(
        default=-1,
        description="Confidence in the prediction (0.0 to 1.0, -1 if unavailable)"
    )
    latency_ms: float
    cost_usd: float = 0.0

    @field_validator("latency_ms")
    @classmethod
    def round_latency(cls, v: float) -> float:
        return round(v, 3)


class Source(BaseModel):
    ticket_id: str
    customer_text: str
    brand_reply: str
    similarity: float


class RetrieveResponse(BaseModel):
    sources: list[Source]
    embedding_backend: Literal["openai", "st"]


class LLMResult(BaseModel):
    response: str
    latency_ms: float
    cost_usd: float

    @field_validator("latency_ms")
    @classmethod
    def round_latency(cls, v: float) -> float:
        return round(v, 3)


class RagGenerateResponse(LLMResult):
    retrieve: RetrieveResponse


class QueryResponse(BaseModel):
    query: str
    sources: list[Source]
    rag_answer: LLMResult
    no_rag_answer: LLMResult
    ml_prediction: PredictPriorityResponse
    llm_prediction: PredictPriorityResponse


class ErrorResponse(BaseModel):
    error: str
    status_code: int
