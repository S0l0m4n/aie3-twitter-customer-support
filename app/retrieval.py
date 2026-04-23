from functools import lru_cache

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

from app.config import CHROMA_DATA_DIR, OPENAI_API_KEY, OPENAI_EMBEDDING_MODEL
from app.schemas import Source

COLLECTION_NAME = "complaints"


@lru_cache(maxsize=1)
def _get_collection():
    embedding_fn = OpenAIEmbeddingFunction(
        api_key=OPENAI_API_KEY,
        model_name=OPENAI_EMBEDDING_MODEL,
    )
    client = chromadb.PersistentClient(path=CHROMA_DATA_DIR)
    return client.get_collection(name=COLLECTION_NAME, embedding_function=embedding_fn)


def retrieve(text: str, top_k: int) -> list[Source]:
    collection = _get_collection()
    results = collection.query(query_texts=[text], n_results=top_k)

    sources = []
    for i in range(len(results["ids"][0])):
        metadata = results["metadatas"][0][i]
        distance = results["distances"][0][i]
        # OpenAI embeddings are unit-normalised; L2 maps to cosine via: similarity = 1 - d²/2
        similarity = round(max(0.0, 1 - (distance ** 2) / 2), 4)
        sources.append(Source(
            ticket_id=metadata["ticket_id"],
            customer_text=results["documents"][0][i],
            brand_reply=metadata["brand_reply"],
            similarity=similarity,
        ))

    return sources