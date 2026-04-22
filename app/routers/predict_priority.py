from fastapi import APIRouter
from app.schemas import PredictPriorityRequest, MLPredictPriorityResponse, LLMPredictPriorityResponse

router = APIRouter(prefix="/predict_priority", tags=["Debug"])


@router.post("/ml", response_model=MLPredictPriorityResponse)
async def predict_priority_ml(request: PredictPriorityRequest):
    raise NotImplementedError


@router.post("/llm", response_model=LLMPredictPriorityResponse)
async def predict_priority_llm(request: PredictPriorityRequest):
    raise NotImplementedError
