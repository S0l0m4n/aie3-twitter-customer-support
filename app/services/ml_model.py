import time
from app.schemas import MLPredictPriorityResponse


def predict_priority(text: str) -> MLPredictPriorityResponse:
    """Run ML priority predictor. Returns MLPredictPriorityResponse."""
    t0 = time.time()
    # TODO: load model.pkl (once at startup), extract features, call predict_proba
    latency_ms = (time.time() - t0) * 1000
    return MLPredictPriorityResponse(label="normal", confidence=0.0, latency_ms=latency_ms)
