import os
from dotenv import load_dotenv

load_dotenv()

# Choose between: "groq", "openai"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")

ML_MODEL = os.getenv("ML_MODEL", "app/ml/priority_classifier.joblib")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

# Switch to "st" to use the sentence-transformers database
EMBEDDING_BACKEND = os.getenv("EMBEDDING_BACKEND", "openai")

if EMBEDDING_BACKEND == "openai":
    CHROMA_DATA_DIR = "./chroma_data"
elif EMBEDDING_BACKEND == "st":
    CHROMA_DATA_DIR = "./chroma_data_st"
else:
    raise ValueError(f"Invalid EMBEDDING_BACKEND: '{EMBEDDING_BACKEND}'. Must be 'openai' or 'st'.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "<your-key>")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

ST_EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
