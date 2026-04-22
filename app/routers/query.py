import time

from fastapi import APIRouter
from app.schemas import QueryRequest, QueryResponse, Source, LLMResult, PredictPriorityResponse
from app.features import extract_features

router = APIRouter(tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    # TODO: implement all-or-nothing orchestration:
    # 1. retrieve: embed request.text, query ChromaDB for top_k sources
    # 2. rag_answer: call Groq with sources as context
    # 3. no_rag_answer: call Groq without context
    # 4. ml_prediction: extract_features + model.pkl predict_proba
    # 5. llm_prediction: call Groq with json_schema strict mode
    # 6. log_query: print JSONL entry to stdout
    raise NotImplementedError