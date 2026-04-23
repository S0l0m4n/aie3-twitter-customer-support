from fastapi import APIRouter

router = APIRouter(tags=["System"])


@router.get("/health")
def health_check():
    """Check API health.

    Returns `{"status": "ok"}` when the service is running.
    """
    return {"status": "ok"}