import time
from app.schemas import Source


def retrieve(text: str, top_k: int) -> tuple[list[Source], float]:
    """Query ChromaDB for similar complaints. Returns (sources, latency_ms)."""
    t0 = time.time()
    # TODO: embed text, query ChromaDB, return Source objects
    latency_ms = (time.time() - t0) * 1000
    return [], latency_ms