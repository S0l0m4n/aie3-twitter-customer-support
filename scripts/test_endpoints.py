"""
End-to-end smoke tests for /retrieve and /generate/rag.
Starts the server, runs several complaint scenarios, prints results.
"""

import json
import subprocess
import time

import requests

BASE = "http://localhost:8001"

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

        print(f"\n--- /retrieve ({retrieve_resp['latency_ms']:.0f} ms embed+query, {retrieve_wall:.0f} ms total) ---")
        for s in sources:
            print(f"  [{s['similarity']:.3f}] ticket {s['ticket_id']}: {s['customer_text'][:80]}")

        # Step 2: generate/rag
        t0 = time.time()
        rag_resp = post("/generate/rag", {"text": complaint, "sources": sources})
        rag_wall = (time.time() - t0) * 1000

        print(f"\n--- /generate/rag ({rag_resp['latency_ms']:.0f} ms LLM, {rag_wall:.0f} ms total) ---")
        print(f"  {rag_resp['response']}")

        # Step 3: generate/no-rag
        t0 = time.time()
        no_rag_resp = post("/generate/no-rag", {"text": complaint})
        no_rag_wall = (time.time() - t0) * 1000

        print(f"\n--- /generate/no-rag ({no_rag_resp['latency_ms']:.0f} ms LLM, {no_rag_wall:.0f} ms total) ---")
        print(f"  {no_rag_resp['response']}")

        results.append({
            "complaint": complaint,
            "sources": sources,
            "rag_response": rag_resp["response"],
            "rag_latency_ms": rag_resp["latency_ms"],
            "no_rag_response": no_rag_resp["response"],
            "no_rag_latency_ms": no_rag_resp["latency_ms"],
            "retrieve_latency_ms": retrieve_resp["latency_ms"],
        })

    return results


if __name__ == "__main__":
    proc = subprocess.Popen(
        [".venv/bin/uvicorn", "main:app", "--port", "8001"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)

    try:
        results = run_tests()
        with open("scripts/test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        print("\n\nResults saved to scripts/test_results.json")
    finally:
        proc.terminate()