import json
import time

from fastapi import APIRouter, HTTPException

import app.llm as llm
from app.ml import model
from app.ml.features import extract_features
from app.prompts.generate import (
    GENERATE_NO_RAG_PROMPT,
    GENERATE_RAG_PROMPT,
    build_rag_user_prompt,
)
from app.prompts.predict_priority import PREDICT_PRIORITY_PROMPT
from app.rag.retrieve import retrieve
from app.schemas import LLMResult, PredictPriorityResponse, QueryRequest, QueryResponse
from app.utils.logger import log_query

router = APIRouter(tags=["Query"])


def _build_llm_priority_user_prompt(query: str) -> str:
    return f'Classify this complaint:\n\n"{query}"'


@router.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Run the full RAG pipeline.

    Orchestrates all services in a single call: retrieves similar tickets,
    generates a RAG reply and a no-RAG baseline reply, and predicts ticket
    priority with both the ML model and the LLM. All services must succeed —
    any failure returns an error with no partial response.
    """
    log_entry: dict = {
        "query": request.text,
        "top_k": request.top_k,
        "errors": [],
    }

    # 1. Retrieve
    try:
        retrieve_result = retrieve(request.text, request.top_k)
    except Exception as e:
        log_entry["errors"].append(f"retrieval: {e}")
        log_query(log_entry)
        raise HTTPException(status_code=503, detail=f"Retrieval failed: {e}")

    sources = retrieve_result.sources
    log_entry["sources"] = [s.model_dump() for s in sources]

    # 2. RAG answer
    try:
        t0 = time.time()
        rag_response = llm.call(build_rag_user_prompt(request.text, sources), GENERATE_RAG_PROMPT)
        rag_latency_ms = (time.time() - t0) * 1000
    except Exception as e:
        log_entry["errors"].append(f"rag_answer: {e}")
        log_query(log_entry)
        raise HTTPException(status_code=503, detail=f"RAG generation failed: {e}")

    rag_answer = LLMResult(response=rag_response, latency_ms=rag_latency_ms, cost_usd=0.0)
    log_entry["rag_answer"] = rag_answer.model_dump()

    # 3. No-RAG answer
    try:
        t0 = time.time()
        no_rag_response = llm.call(request.text, GENERATE_NO_RAG_PROMPT)
        no_rag_latency_ms = (time.time() - t0) * 1000
    except Exception as e:
        log_entry["errors"].append(f"no_rag_answer: {e}")
        log_query(log_entry)
        raise HTTPException(status_code=503, detail=f"No-RAG generation failed: {e}")

    no_rag_answer = LLMResult(response=no_rag_response, latency_ms=no_rag_latency_ms, cost_usd=0.0)
    log_entry["no_rag_answer"] = no_rag_answer.model_dump()

    # 4. ML prediction
    if not model.is_loaded():
        log_entry["errors"].append("ml_prediction: model not loaded")
        log_query(log_entry)
        raise HTTPException(status_code=503, detail="ML model not loaded")

    try:
        t0 = time.time()
        features = extract_features(request.text)
        ml_label, ml_confidence = model.predict_with_proba(features)
        ml_latency_ms = (time.time() - t0) * 1000
    except RuntimeError as e:
        log_entry["errors"].append(f"ml_prediction: {e}")
        log_query(log_entry)
        raise HTTPException(status_code=500, detail=str(e))

    ml_prediction = PredictPriorityResponse(
        label=ml_label,
        confidence=ml_confidence,
        latency_ms=ml_latency_ms,
        cost_usd=0.0,
    )
    log_entry["ml_prediction"] = {"label": ml_label, "confidence": ml_confidence, "latency_ms": ml_latency_ms}

    # 5. LLM prediction
    try:
        t0 = time.time()
        llm_priority_str = llm.call(
            _build_llm_priority_user_prompt(request.text),
            PREDICT_PRIORITY_PROMPT,
            response_model=PredictPriorityResponse,
        )
        llm_latency_ms = (time.time() - t0) * 1000
    except Exception as e:
        log_entry["errors"].append(f"llm_prediction: {e}")
        log_query(log_entry)
        raise HTTPException(status_code=503, detail=f"LLM priority prediction failed: {e}")

    llm_data = json.loads(llm_priority_str)
    llm_prediction = PredictPriorityResponse(
        label=llm_data["label"],
        confidence=llm_data.get("confidence", -1),
        latency_ms=llm_latency_ms,
        cost_usd=0.0,
    )
    log_entry["llm_prediction"] = {
        "label": llm_data["label"],
        "confidence": llm_data.get("confidence", -1),
        "latency_ms": llm_latency_ms,
    }

    log_query(log_entry)

    return QueryResponse(
        query=request.text,
        sources=sources,
        rag_answer=rag_answer,
        no_rag_answer=no_rag_answer,
        ml_prediction=ml_prediction,
        llm_prediction=llm_prediction,
    )
