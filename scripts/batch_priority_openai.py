"""
Batch priority classification using OpenAI Batch API.

Usage:
  1. Generate the batch input file:
     python3 scripts/batch_priority_openai.py prepare --csv test_set.csv

  2. Submit the batch:
     python3 scripts/batch_priority_openai.py submit --input batch_input.jsonl

  3. Check status:
     python3 scripts/batch_priority_openai.py status --batch-id batch_abc123

  4. Download results:
     python3 scripts/batch_priority_openai.py download --batch-id batch_abc123 --output batch_output.jsonl

  5. Parse results and compare with actuals:
     python3 scripts/batch_priority_openai.py compare --csv test_set.csv --output batch_output.jsonl

Requires: OPENAI_API_KEY environment variable
"""

import argparse
import csv
import json
import sys
import os
from openai import OpenAI
from sklearn.metrics import accuracy_score, classification_report

SYSTEM_PROMPT = """\
You are a ticket triage system. You classify customer support complaints as either "urgent" or "normal".

A ticket is urgent if it involves financial loss, account security, service outage, time pressure, or if the customer is expressing strong frustration or distress. Otherwise it is normal. When in doubt, lean urgent
"""

USER_PROMPT_TEMPLATE = "Classify this prompt:\n{query}"

MODEL = "gpt-4o-mini"  # cheap, fast, good enough for classification


def prepare(args):
    """Step 1: Read CSV, generate batch_input.jsonl"""
    count = 0
    with open(args.csv, "r", encoding="utf-8") as f_in, \
         open(args.input, "w", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        for row in reader:
            text = row["text"]
            idx = row.get("", row.get("Unnamed: 0", str(count)))  # handle index column

            request = {
                "custom_id": f"req-{idx}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(query=text)},
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "priority",
                            "strict": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "label": {
                                        "type": "string",
                                        "enum": ["urgent", "normal"]
                                    },
                                    "confidence": {
                                        "type": "number",
                                        "description": "Confidence from 0.0 to 1.0"
                                    }
                                },
                                "required": ["label", "confidence"],
                                "additionalProperties": False
                            }
                        }
                    },
                    "max_tokens": 50,
                },
            }
            f_out.write(json.dumps(request) + "\n")
            count += 1

    print(f"Wrote {count} requests to {args.input}")


def submit(args):
    """Step 2: Upload JSONL and create batch"""
    client = OpenAI()

    print(f"Uploading {args.input}...")
    with open(args.input, "rb") as f:
        batch_file = client.files.create(file=f, purpose="batch")
    print(f"File ID: {batch_file.id}")

    print("Creating batch...")
    batch = client.batches.create(
        input_file_id=batch_file.id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={"description": "priority classification eval"}
    )
    print(f"Batch ID: {batch.id}")
    print(f"Status: {batch.status}")
    print(f"\nRun:\npython3 scripts/batch_priority_openai.py status --batch-id {batch.id}")


def status(args):
    """Step 3: Check batch status"""
    client = OpenAI()
    batch = client.batches.retrieve(args.batch_id)

    print(f"Status: {batch.status}")
    print(f"Total: {batch.request_counts.total}")
    print(f"Completed: {batch.request_counts.completed}")
    print(f"Failed: {batch.request_counts.failed}")

    if batch.status == "completed":
        print(f"\nOutput file ID: {batch.output_file_id}")
        print(f"Run: python3 scripts/batch_priority_openai.py download --batch-id {args.batch_id} --output batch_output.jsonl")


def download(args):
    """Step 4: Download results"""
    client = OpenAI()
    batch = client.batches.retrieve(args.batch_id)

    if batch.status != "completed":
        print(f"Batch not complete yet. Status: {batch.status}")
        return

    content = client.files.content(batch.output_file_id)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content.text)

    print(f"Results saved to {args.output}")
    print(f"Run: python3 scripts/batch_priority_openai.py compare --csv test_set.csv --output {args.output}")


def compare(args):
    """Step 5: Parse results, write CSV, and print full classification report"""
    # Load actual labels and text from CSV
    actuals = {}
    texts = {}
    with open(args.csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = row.get("", row.get("Unnamed: 0", ""))
            key = f"req-{idx}"
            actuals[key] = row["priority"]
            texts[key] = row["text"]

    # Parse batch output
    predictions = {}
    confidences = {}
    errors = 0
    with open(args.output, "r", encoding="utf-8") as f:
        for line in f:
            result = json.loads(line)
            custom_id = result["custom_id"]

            if result.get("error"):
                errors += 1
                continue

            content = result["response"]["body"]["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            predictions[custom_id] = parsed["label"]
            confidences[custom_id] = parsed.get("confidence", "")

    # Build aligned results
    rows = []
    y_true = []
    y_pred = []
    for custom_id in sorted(predictions.keys(), key=lambda x: int(x.split("-", 1)[1])):
        if custom_id not in actuals:
            continue
        actual = actuals[custom_id]
        predicted = predictions[custom_id]
        rows.append({
            "custom_id": custom_id,
            "text": texts.get(custom_id, ""),
            "actual": actual,
            "predicted": predicted,
            "confidence": confidences.get(custom_id, ""),
            "correct": actual == predicted,
        })
        y_true.append(actual)
        y_pred.append(predicted)

    # Write results CSV
    with open(args.results_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["custom_id", "text", "actual", "predicted", "confidence", "correct"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Per-row results saved to {args.results_csv}\n")

    print(f"{len(rows)} matched, {errors} errors\n")
    print(classification_report(y_true, y_pred, target_names=["normal", "urgent"]))
    print(f"Accuracy: {accuracy_score(y_true, y_pred):.4f}")


def main():
    parser = argparse.ArgumentParser(
        description="Batch priority classification",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""Steps:
        python3 scripts/batch_priority_openai.py prepare --csv test_set.csv
        python3 scripts/batch_priority_openai.py submit --input batch_input.jsonl
        python3 scripts/batch_priority_openai.py status --batch-id <id_from_previous_step>
        python3 scripts/batch_priority_openai.py download --batch-id <id> --output batch_output.jsonl
        python3 scripts/batch_priority_openai.py compare --csv test_set.csv --output batch_output.jsonl
        """
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_prepare = subparsers.add_parser("prepare")
    p_prepare.add_argument("--csv", required=True)
    p_prepare.add_argument("--input", default="batch_input.jsonl")

    p_submit = subparsers.add_parser("submit")
    p_submit.add_argument("--input", default="batch_input.jsonl")

    p_status = subparsers.add_parser("status")
    p_status.add_argument("--batch-id", required=True)

    p_download = subparsers.add_parser("download")
    p_download.add_argument("--batch-id", required=True)
    p_download.add_argument("--output", default="batch_output.jsonl")

    p_compare = subparsers.add_parser("compare")
    p_compare.add_argument("--csv", required=True)
    p_compare.add_argument("--output", default="batch_output.jsonl")
    p_compare.add_argument("--results-csv", default="batch_results.csv")

    args = parser.parse_args()
    {"prepare": prepare, "submit": submit, "status": status,
     "download": download, "compare": compare}[args.command](args)


if __name__ == "__main__":
    main()
