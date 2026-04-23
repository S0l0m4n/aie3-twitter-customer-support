"""
Embeds complaint text from pairs.csv into ChromaDB using Gemini text-embedding-004.

Requires GOOGLE_API_KEY in .env.
Output: data/chroma_data/ (ChromaDB persistent directory)
"""

import os
import re

import chromadb
import pandas as pd
from chromadb.utils.embedding_functions import GoogleGenerativeAiEmbeddingFunction
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

INPUT = "data/first-brand-reply-pairs.csv"
CHROMA_DIR = "chroma_data"
COLLECTION_NAME = "complaints"
BATCH_SIZE = 500


def clean_text(text: str) -> str:
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return text.strip()


def print_available_models():
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

    print("Available models: ")
    for model in genai.list_models():
        print(model.name + " ")
    print()


df = pd.read_csv(INPUT)
print(f"Loaded {len(df):,} pairs")

dupes = df[df.duplicated(subset="ticket_id", keep=False)]
if len(dupes) > 0:
    print(f"Duplicate ticket_ids: {len(dupes):,} rows — " \
          f"example indices: {dupes.index[:5].tolist()}")
df = df.drop_duplicates(subset="ticket_id")

df["cleaned_text"] = df["complaint_text"].astype(str).apply(clean_text)

empties = df[df["cleaned_text"] == ""]
if len(empties) > 0:
    print(f"Empty after cleaning: {len(empties):,} rows — " \
          f"example indices: {empties.index[:5].tolist()}")
df = df[df["cleaned_text"] != ""].copy().reset_index(drop=True)

# Rename final version of original text column
df = df.drop(columns="complaint_text")
df = df.rename(columns={"cleaned_text": "complaint_text"})

print(f"After dedup and cleaning: {len(df):,} rows")

embedding_fn = GoogleGenerativeAiEmbeddingFunction(
    api_key=os.environ["GEMINI_API_KEY"],
    model_name=os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
)

client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = client.get_or_create_collection(
        name=COLLECTION_NAME, embedding_function=embedding_fn)

total = len(df)
if collection.count() == total:
    print(f"Collection already contains {total:,} documents, skipping.")
    exit(0)

for start in range(0, total, BATCH_SIZE):
    batch = df.iloc[start : start + BATCH_SIZE]
    collection.upsert(
        ids=[f"t_{row.ticket_id}" for row in batch.itertuples()],
        documents=batch["complaint_text"].tolist(),
        metadatas=[
            {
                "brand_reply": str(row.brand_reply),
                "ticket_id": str(row.ticket_id),
            }
            for row in batch.itertuples()
        ],
    )
    print(f"Upserted {min(start + BATCH_SIZE, total):,} / {total:,}")

print("Done.")
