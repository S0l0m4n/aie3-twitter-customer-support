"""
Embeds complaint text from pairs.csv into ChromaDB using sentence-transformers.

Output: chroma_data/ (ChromaDB persistent directory)
"""

import os
import re

import chromadb
import pandas as pd
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

INPUT = "data/first-brand-reply-pairs.csv"
CHROMA_DIR = "chroma_data_st"
COLLECTION_NAME = "complaints"
BATCH_SIZE = 1000
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")


def clean_text(text: str) -> str:
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"https?://\S+", "", text)
    return text.strip()


df = pd.read_csv(INPUT)
print(f"Loaded {len(df):,} pairs")

dupes = df[df.duplicated(subset="ticket_id", keep=False)]
if len(dupes) > 0:
    print(f"Duplicate ticket_ids: {len(dupes):,} rows — "
          f"example indices: {dupes.index[:5].tolist()}")
df = df.drop_duplicates(subset="ticket_id")

df["cleaned_text"] = df["complaint_text"].astype(str).apply(clean_text)

empties = df[df["cleaned_text"] == ""]
if len(empties) > 0:
    print(f"Empty after cleaning: {len(empties):,} rows — "
          f"example indices: {empties.index[:5].tolist()}")
df = df[df["cleaned_text"] != ""].copy().reset_index(drop=True)
# NOTE: Empty indices result from complaints that were just an @mention and URL
# with no actual text, e.g. "@AzureSupport https://t.co/oePAzLijRF".

# Rename final version of original text column
df = df.drop(columns="complaint_text")
df = df.rename(columns={"cleaned_text": "complaint_text"})

print(f"After dedup and cleaning: {len(df):,} rows")

embedding_fn = SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
print(f"Loaded model: {MODEL_NAME}")

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
