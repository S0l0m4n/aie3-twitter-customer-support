from fastapi import APIRouter
from app.schemas import QueryRequest, RetrieveResponse
from app.rag.retrieve import retrieve

router = APIRouter(tags=["Debug"])


@router.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_sources(request: QueryRequest):
    """Retrieve similar support tickets.

    Embeds the query text and returns the `top_k` most similar tickets from
    the ChromaDB vector store, along with the embedding backend that was used.
    """
    return retrieve(request.text, request.top_k)
