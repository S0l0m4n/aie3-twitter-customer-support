from fastapi import APIRouter
from app.schemas import QueryRequest, RetrieveResponse

router = APIRouter(tags=["Debug"])


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(request: QueryRequest):
    raise NotImplementedError