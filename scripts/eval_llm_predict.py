"""
Evaluate zero-shot LLM priority classification on a stratified sample of test_set.csv.

Key design decisions:
  - Stratified sample — preserves the ~93/7 normal/urgent split from the full test set
  - Calls OpenAI directly with json_schema structured output — bypasses app.llm which
    does not pass response_model through to OpenAI
  - No artificial rate-limit delay; OpenAI's RPM limits are well above what 4 workers need

Usage:
    python3 scripts/eval_llm_predict.py
    python3 scripts/eval_llm_predict.py --sample 100 --workers 5
"""

import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
from typing import Literal

import pandas as pd
from openai import OpenAI
from pydantic import BaseModel
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.prompts.predict_priority import PREDICT_PRIORITY_PROMPT

TEST_CSV = "data/test_set.csv"
DEFAULT_SAMPLE = 200
DEFAULT_WORKERS = 4


class _Priority(BaseModel):
    label: Literal["normal", "urgent"]


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)


def classify(text: str) -> str:
    response = _get_client().chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": PREDICT_PRIORITY_PROMPT},
            {"role": "user", "content": f"Classify this prompt:\n{text}"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": _Priority.__name__,
                "strict": True,
                "schema": _Priority.model_json_schema(),
            },
        },
        max_tokens=50,
    )
    data = json.loads(response.choices[0].message.content)
    return data["label"]


def main(sample: int, workers: int):
    df = pd.read_csv(TEST_CSV)

    # Stratified sample to preserve class balance
    df_sample, _ = train_test_split(df, train_size=sample, stratify=df["priority"], random_state=42)

    print(f"Sample size: {len(df_sample)}  "
          f"(urgent: {(df_sample['priority'] == 'urgent').sum()}, "
          f"normal: {(df_sample['priority'] == 'normal').sum()})")
    print(f"Model: {OPENAI_MODEL}  Workers: {workers}\n")

    predictions = {}
    t0 = time.time()

    def _call(idx: int, text: str) -> tuple[int, str]:
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