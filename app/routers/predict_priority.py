import time

from fastapi import APIRouter
from app.schemas import PredictPriorityRequest, MLPredictPriorityResponse, LLMPredictPriorityResponse
from app.features import extract_features

router = APIRouter(prefix="/predict_priority", tags=["Debug"])


@router.post("/ml", response_model=MLPredictPriorityResponse)
async def predict_priority_ml(request: PredictPriorityRequest):
    t0 = time.time()
    # TODO: load model.pkl (once at startup), call extract_features, then predict_proba
    features = extract_features(request.text)
    latency_ms = (time.time() - t0) * 1000
    return MLPredictPriorityResponse(label="normal", confidence=0.0, latency_ms=latency_ms)


@router.post("/llm", response_model=LLMPredictPriorityResponse)
async def predict_priority_llm(request: PredictPriorityRequest):
    t0 = time.time()
    # TODO: call Groq with json_schema strict mode, parse label + confidence
    latency_ms = (time.time() - t0) * 1000
    return LLMPredictPriorityResponse(label="normal", confidence=0.0, latency_ms=latency_ms, cost_usd=0.0)