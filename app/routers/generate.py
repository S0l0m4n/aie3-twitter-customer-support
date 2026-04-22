from fastapi import APIRouter
from app.schemas import RagGenerateRequest, PredictPriorityRequest, RagGenerateResponse, NoRagGenerateResponse

router = APIRouter(prefix="/generate", tags=["Debug"])


@router.post("/rag", response_model=RagGenerateResponse)
async def generate_rag(request: RagGenerateRequest):
    raise NotImplementedError


@router.post("/no-rag", response_model=NoRagGenerateResponse)
async def generate_no_rag(request: PredictPriorityRequest):
    raise NotImplementedError