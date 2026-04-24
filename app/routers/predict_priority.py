import json
import logging
import time

from fastapi import APIRouter, HTTPException

import app.llm as llm
from app.ml import model
from app.ml.features import extract_features
from app.prompts.predict_priority import PREDICT_PRIORITY_PROMPT
from app.schemas import (
    PredictPriorityResponse,
    PredictPriorityResponse,
    QueryRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predict_priority", tags=["Debug"])


def build_predict_priority_user_prompt(query: str) -> str:
    return f"Classify this prompt:\n{query}"


@router.post("/ml", response_model=PredictPriorityResponse)
async def predict_priority_ml(request: QueryRequest):
    """Predict ticket priority using the ML model.

    Extracts hand-crafted features from the query text and runs them through
    the trained `model.pkl` classifier to predict `normal` or `urgent`.
    """
    if not model.is_loaded():
        raise HTTPException(status_code=503, detail="Model not loaded.")

    t0 = time.time()

    # Extract features from input query that the model needs to predict priority
    features = extract_features(request.text)

    try:
        y = model.predict(features)
    except RuntimeError as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))

    latency_ms = (time.time() - t0) * 1000

    response = PredictPriorityResponse(
        label=y,
        latency_ms=latency_ms,
        cost_usd=0.0,  # ML model is free
    )
    return response


@router.post("/llm", response_model=PredictPriorityResponse)
async def predict_priority_llm(request: QueryRequest):
    """Predict ticket priority using the LLM.

    Asks the LLM to classify the query as `normal` or `urgent` using a
    structured JSON response. Useful as a baseline against the ML model.
    """
    t0 = time.time()
    llm_response_str = llm.call(
        build_predict_priority_user_prompt(request.text),
        PREDICT_PRIORITY_PROMPT,
        response_model=PredictPriorityResponse,
    )
    latency_ms = (time.time() - t0) * 1000

    # Parse the LLM response (assumes it returns at least {"label": "..."})
    llm_data = json.loads(llm_response_str)

    # Construct the full response, setting defaults/additional fields
    response = PredictPriorityResponse(
        label=llm_data["label"],
        latency_ms=latency_ms,
        cost_usd=0.0,  # Fixed cost for now
    )
    return response
