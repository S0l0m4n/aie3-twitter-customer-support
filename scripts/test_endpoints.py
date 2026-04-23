"""
End-to-end smoke tests for /retrieve and /generate/rag.
Assumes the server is already running. Start it with:
    uvicorn main:app --port 8000
"""

import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "http://localhost:8000"

TEST_COMPLAINTS = [
    "I was charged twice this month and nobody is responding to my emails",
    "My account has been hacked and someone changed my password",
    "Your app has been down for 3 hours, I can't access anything",
    "I cancelled my subscription last week but you still charged me",
    "The product I received is completely broken and I want a refund immediately",
]


def post(path, body):
    r = requests.post(f"{BASE}{path}", json=body, timeout=30)
    r.raise_for_status()
    return r.json()


def run_tests():
    results = []

    for complaint in TEST_COMPLAINTS:
        print(f"\n{'='*60}")
        print(f"COMPLAINT: {complaint}")
        print("="*60)

        # Step 1: retrieve
        t0 = time.time()
        retrieve_resp = post("/retrieve", {"text": complaint, "top_k": 3})
        retrieve_wall = (time.time() - t0) * 1000
        sources = retrieve_resp["sources"]

        print(f"\n--- /retrieve ({retrieve_wall:.0f} ms) ---")
        for s in sources:
            print(f"  [{s['similarity']:.3f}] ticket {s['ticket_id']}: {s['customer_text'][:80]}")

        # Step 2: generate/rag
        t0 = time.time()
        rag_resp = post("/generate/rag", {"text": complaint})
        rag_wall = (time.time() - t0) * 1000

        print(f"\n--- /generate/rag ({rag_wall:.0f} ms) ---")
        print(f"  {rag_resp['response']}")

        # Step 3: generate/no-rag
        t0 = time.time()
        no_rag_resp = post("/generate/no-rag", {"text": complaint})
        no_rag_wall = (time.time() - t0) * 1000

        print(f"\n--- /generate/no-rag ({no_rag_wall:.0f} ms) ---")
        print(f"  {no_rag_resp['response']}")

        results.append({
            "complaint": complaint,
            "sources": sources,
            "rag_response": rag_resp["response"],
            "rag_latency_ms": rag_wall,
            "no_rag_response": no_rag_resp["response"],
            "no_rag_latency_ms": no_rag_wall,
        })

    return results


if __name__ == "__main__":
    try:
        requests.get(f"{BASE}/health", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"Server not running at {BASE}. Start it with:\n  uvicorn main:app --port 8000")
        sys.exit(1)

    results = run_tests()
    with open("scripts/test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n\nResults saved to scripts/test_results.json")
