"""
Evaluate zero-shot LLM priority classification on a stratified sample of test_set.csv.

Key design decisions:
  - Stratified sample — preserves the ~93/7 normal/urgent split from the full test set
  - Rate limiting — REQUEST_DELAY of ~2.1s per worker keeps 4 workers at ~28 RPM, safely under the 30 RPM cap. With 4
  workers and 200 rows that's about 1.5 min (200 × 2.1s / 4)
  - Reuses app.llm.call directly — no need to spin up the FastAPI server
  - No structured output (response_model=None) since we only need the label field, but it still parses the JSON response

Usage:
    python scripts/eval_llm.py
    python scripts/eval_llm.py --sample 100 --workers 5
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

import pandas as pd
from pydantic import BaseModel
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging

from app.llm import call
from app.prompts.predict_priority import PREDICT_PRIORITY_PROMPT

logging.getLogger("app.llm").setLevel(logging.WARNING)


class _Priority(BaseModel):
    label: Literal["normal", "urgent"]

TEST_CSV = "data/test_set.csv"
# Stay safely under Groq's 30 RPM free tier limit
DEFAULT_SAMPLE = 200
DEFAULT_WORKERS = 4
# Minimum seconds between requests per worker to avoid bursting over the limit
REQUEST_DELAY = 60 / 28  # ~2.1s → 28 req/min across all workers


def classify(text: str) -> str:
    response_str = call(
        user_prompt=f"Classify this prompt:\n{text}",
        system_prompt=PREDICT_PRIORITY_PROMPT,
        response_model=_Priority,
    )
    data = json.loads(response_str)
    return data["label"]


def main(sample: int, workers: int):
    df = pd.read_csv(TEST_CSV)

    # Stratified sample to preserve class balance
    df_sample, _ = train_test_split(df, train_size=sample, stratify=df["priority"], random_state=42)

    print(f"Sample size: {len(df_sample)}  "
          f"(urgent: {(df_sample['priority'] == 'urgent').sum()}, "
          f"normal: {(df_sample['priority'] == 'normal').sum()})")
    print(f"Workers: {workers}  ~{workers / REQUEST_DELAY * 60:.0f} effective RPM\n")

    predictions = {}
    t0 = time.time()

    def _call(idx: int, text: str) -> tuple[int, str]:
        time.sleep(REQUEST_DELAY)
        label = classify(text)
        return idx, label

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_call, i, row["text"]): i
            for i, row in df_sample.iterrows()
        }
        completed = 0
        for future in as_completed(futures):
            idx, label = future.result()
            predictions[idx] = label
            completed += 1
            print(f"\r{completed}/{len(df_sample)}", end="", flush=True)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s\n")

    y_true = df_sample["priority"].tolist()
    y_pred = [predictions[i] for i in df_sample.index]

    print(classification_report(y_true, y_pred, target_names=["normal", "urgent"]))
    print(f"Accuracy : {accuracy_score(y_true, y_pred):.3f}")
    print(f"Urgent F1: {f1_score(y_true, y_pred, pos_label='urgent'):.3f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=DEFAULT_SAMPLE)
    parser.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = parser.parse_args()
    main(args.sample, args.workers)
