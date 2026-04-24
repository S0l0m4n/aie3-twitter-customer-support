import logging

from fastapi import FastAPI

from app.ml import model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-18s | %(levelname)-5s | %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.WARNING)

from app.routers import query, retrieve, generate, predict_priority, health

app = FastAPI(
    title="Twitter Customer Support",
    description="RAG-powered customer support triage with ML + LLM priority prediction.",
    version="1.0.0",
)


@app.on_event("startup")
def startup():
    try:
        model.load_model()
    except FileNotFoundError as e:
        # Allow the server to start without the model: /predict will raise error
        print(f"WARNING: {e}")


app.include_router(query.router)
app.include_router(retrieve.router)
app.include_router(generate.router)
app.include_router(predict_priority.router)
app.include_router(health.router)
