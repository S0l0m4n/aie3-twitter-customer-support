# twitter-customer-support — Architecture Spec

---

## 1. Technology Stack

| Layer | Choice | Detail |
|---|---|---|
| **LLM** | `openai/gpt-oss-20b` via Groq | Single model for all three LLM calls (RAG answer, non-RAG answer, zero-shot priority). Free tier, no credit card required. Rate limit: 30 req/min, 6,000 tokens/min. |
| **LLM API** | OpenAI-compatible | `openai` Python client with `base_url="https://api.groq.com/openai/v1"`. Uses `json_schema` with `strict: true` for the priority prediction call. |
| **ML models** | scikit-learn | Train 3+ classifiers (Logistic Regression, Random Forest, XGBoost). Export best as `model.pkl`. |
| **Backend** | FastAPI | Async, Pydantic schemas, clearly separated routers. |
| **Frontend** | React | Single-page app, no routing, no state management library. `useState` + one `fetch` call. |
| **Orchestration** | Docker Compose | Two services: `backend` and `frontend`. Named volume for ChromaDB data and logs. |
| **Vector store** | ChromaDB in-process | Runs as a Python library inside the backend container. Data persisted to a directory on disk via a Docker named volume. No separate service, no network calls. |
| **Embedding model** | Hosted embeddings model | Use OpenAI or Gemini embeddings model, e.g. `text-embedding-004` by Gemini. Free generous tier, needs 768 dimensions. |

---

## 2. Data Layer

### 2.1 Source Dataset

Kaggle: Customer Support on Twitter (`thoughtvector/customer-support-on-twitter`). Key columns: `tweet_id`, `author_id`, `inbound`, `text`, `created_at`, `response_tweet_id`.

### 2.2 Filtering Strategy

1. Keep only inbound tweets (`inbound == True`) — these are customer complaints.
2. From those, keep only tweets that **start** a conversation — i.e., the tweet is not a follow-up from the same customer. It should not appear as a `response_tweet_id` from another inbound tweet.
3. For each initial complaint, look up the brand's direct reply via `response_tweet_id`.
4. Drop any complaint that has no brand response — nothing useful for RAG context.
5. Sample 20–30k from what remains.

Result: a clean set of first-complaint → first-response pairs.

### 2.3 Chunk Strategy

One tweet = one document in ChromaDB. Tweets are short (~280 chars max), no further splitting needed.

### 2.4 What Gets Stored in ChromaDB

For each of the 20–30k pairs:

- **Embedded and searchable:** the customer complaint text
- **Stored as metadata:** the brand response, the original `tweet_id`

At retrieval time, a match returns both the complaint and the brand reply as a pair.

### 2.5 Labeling Function

Binary classification: `urgent` or `normal`. No priority levels, no categories.

A ticket is **urgent** if any of the following are true:

- Contains any urgency keyword: `refund`, `cancel`, `broken`, `charged`, `stolen`, `hacked`, `urgent`, `asap`, `immediately`, `emergency`, `help`
- Has 2+ exclamation marks
- ALL-CAPS word ratio > 30%

Everything else is **normal**.

This is weak supervision. The ML model may learn to reproduce this rule rather than learn true urgency. This must be documented honestly in the notebook and README.

### 2.6 Feature Engineering

9 features, implemented in a shared `features.py`:

| # | Feature | Type | Rationale |
|---|---|---|---|
| 1 | `word_count` | int | Longer complaints may indicate more serious issues |
| 2 | `char_count` | int | Raw text length as a complexity signal |
| 3 | `exclamation_count` | int | Emotional intensity marker |
| 4 | `question_mark_count` | int | Distinguishes questions from complaints |
| 5 | `caps_ratio` | float | ALL-CAPS indicates shouting / frustration |
| 6 | `urgency_keyword_count` | int | Direct urgency signal from predefined list |
| 7 | `negative_keyword_count` | int | Severity signal beyond the urgency list |
| 8 | `sentiment_compound` | float | VADER compound score — captures overall tone |
| 9 | `has_mention` | bool→int | @mentioning a company suggests escalation |

Keyword lists:

```python
URGENCY_KEYWORDS = {"refund", "cancel", "broken", "charged", "stolen", "hacked",
                     "urgent", "asap", "immediately", "emergency", "help"}

NEGATIVE_KEYWORDS = {"worst", "terrible", "horrible", "awful", "unacceptable",
                      "disgusting", "scam", "fraud", "pathetic"}
```

### 2.7 ML Training

- 80/20 stratified train/test split (classes will be imbalanced — most tickets are "normal")
- Train at least 3 models: Logistic Regression, Random Forest, XGBoost
- Evaluate with appropriate metrics for imbalanced data (precision, recall, F1, confusion matrix)
- Export best model as `model.pkl`
- Document which model won and why

### 2.8 Embedding Pipeline

- Use Gemini `text-embedding-004` or similar to embed all 20–30k complaint texts
- Store in ChromaDB with persistent directory
- The ChromaDB data directory is later mounted into the backend Docker container via a named volume

---

## 3. API Contract

### 3.1 Primary Endpoint

The frontend calls this single endpoint. The backend orchestrates all services internally.

**`POST /query`**

Request:

```json
{
  "text": "I've been charged twice this month and nobody is responding to my emails",
  "top_k": 3
}
```

`top_k` is optional, defaults to 3.

Response:

```json
{
  "query": "I've been charged twice this month and nobody is responding to my emails",

  "sources": [
    {
      "ticket_id": "t_1042",
      "customer_text": "I was charged twice last month and support ignored me",
      "brand_reply": "Sorry about that! Please DM us your account details and we'll issue a refund",
      "similarity": 0.91
    }
  ],

  "rag_answer": {
    "response": "I apologize for the inconvenience with the double charge...",
    "latency_ms": 1100,
    "cost_usd": 0.0008
  },

  "no_rag_answer": {
    "response": "I'm sorry to hear about the double charge...",
    "latency_ms": 780,
    "cost_usd": 0.0005
  },

  "ml_prediction": {
    "label": "urgent",
    "confidence": 0.87,
    "latency_ms": 1.8,
    "cost_usd": 0.0
  },

  "llm_prediction": {
    "label": "urgent",
    "confidence": 0.92,
    "latency_ms": 320,
    "cost_usd": 0.0003
  }
}
```

### 3.2 Debug / Testing Endpoints

For testing individual services in isolation. The frontend does not use them. All accept `{ "text": "..." }` and are self-contained. No endpoint calls another endpoint — they share service functions at the code level.

| Endpoint | Returns | Accepts `top_k` |
|---|---|---|
| `POST /retrieve` | `{ sources }` | Yes |
| `POST /generate/rag` | `{ response, sources, latency_ms, cost_usd }` | Yes |
| `POST /generate/no-rag` | `{ response, latency_ms, cost_usd }` | No |
| `POST /predict/ml` | `{ label, confidence, latency_ms, cost_usd }` | No |
| `POST /predict/llm` | `{ label, confidence, latency_ms, cost_usd }` | No |
| `GET /health` | `{ status: "ok" }` | — |

### 3.3 Response Field Definitions

| Field | Definition |
|---|---|
| `similarity` | Cosine similarity from ChromaDB, float 0–1 |
| `ml_prediction.confidence` | `predict_proba` from scikit-learn — calibrated |
| `llm_prediction.confidence` | Self-reported by the model via structured output — uncalibrated, documented as such |
| `cost_usd` | Calculated from Groq production pricing using token counts from the API response, not free tier pricing |
| `latency_ms` | Wall-clock `time.time()` around each service call, in milliseconds |

All fields are always present. Failures return an error response, not partial data.

---

## 4. Prompt Design

### 4.1 RAG Answer

**System prompt (static):**

```
You are a customer support assistant. You help support agents draft responses to customer complaints.

You will be given a new customer complaint and a set of similar past tickets with their resolutions. Use the patterns and resolution strategies from these past tickets to draft a helpful, professional response to the new complaint.

Do not copy past responses verbatim. Synthesize a new response appropriate to the specific complaint. Keep your response concise — 2-3 sentences max.
```

**User prompt (constructed at runtime):**

```python
def build_rag_user_prompt(query, sources):
    context = "## Similar past tickets\n\n"
    for i, source in enumerate(sources, 1):
        context += f"Ticket {i} (similarity: {source['similarity']:.2f}):\n"
        context += f"Customer: \"{source['customer_text']}\"\n"
        context += f"Resolution: \"{source['brand_reply']}\"\n\n"

    context += "## New complaint\n\n"
    context += f"\"{query}\"\n\n"
    context += "Draft a response to this complaint."

    return context
```

### 4.2 Non-RAG Answer

**System prompt (static):**

```
You are a customer support assistant. You help support agents draft responses to customer complaints.

Draft a helpful, professional response to the following complaint. Keep your response concise — 2-3 sentences max.
```

### 4.3 Zero-shot Priority Prediction

**System prompt (static):**

```
You are a ticket triage system. You classify customer support complaints as either "urgent" or "normal".

A ticket is urgent if it involves financial loss, account security, service outages, or if the customer expresses extreme frustration. Otherwise it is normal.
```

**User prompt (constructed at runtime):**

```python
def build_priority_user_prompt(query):
    return f"Classify this complaint:\n\n\"{query}\""
```

**Structured output schema (via Groq `json_schema`, `strict: true`):**

```json
{
  "type": "object",
  "properties": {
    "label": {
      "type": "string",
      "enum": ["urgent", "normal"]
    },
    "confidence": {
      "type": "number",
      "description": "How confident you are in this classification, from 0.0 to 1.0"
    }
  },
  "required": ["label", "confidence"]
}
```

### 4.4 Prompt Design Decisions

| Decision | Rationale |
|---|---|
| 2-3 sentence cap | Agents need quick drafts, not essays. Keeps token usage low. |
| Labeling rule excluded from zero-shot prompt | ML model learns from rule-based labels. LLM classifies from its own understanding. This is the comparison the brief asks for. |
| Similarity scores in RAG prompt | Tells the LLM how much to trust each example. |
| Same system prompt structure for RAG and non-RAG | Keeps the comparison fair — only variable is whether context is present. |

---

## 5. Logging Schema

Every call to `/query` writes one JSON object to a log file. The log file is stored in a `logs/` directory, persisted via a Docker named volume.

```json
{
  "timestamp": "2026-04-24T02:14:33.012Z",
  "query": "I've been charged twice this month and nobody is responding",
  "top_k": 3,

  "sources": [
    {
      "ticket_id": "t_1042",
      "customer_text": "I was charged twice last month...",
      "brand_reply": "Sorry about that...",
      "similarity": 0.91
    }
  ],

  "rag_answer": {
    "response": "I apologize for...",
    "latency_ms": 1100,
    "cost_usd": 0.0008,
    "tokens_in": 320,
    "tokens_out": 58
  },

  "no_rag_answer": {
    "response": "I'm sorry to hear...",
    "latency_ms": 780,
    "cost_usd": 0.0005,
    "tokens_in": 45,
    "tokens_out": 52
  },

  "ml_prediction": {
    "label": "urgent",
    "confidence": 0.87,
    "latency_ms": 1.8
  },

  "llm_prediction": {
    "label": "urgent",
    "confidence": 0.92,
    "latency_ms": 320,
    "cost_usd": 0.0003,
    "tokens_in": 62,
    "tokens_out": 18
  },

  "errors": []
}
```

Key details:

- One JSON object per line (JSONL format) — easy to parse, grep, and load into pandas later.
- `tokens_in` and `tokens_out` come from the Groq API response's `usage` field. These are used to calculate `cost_usd`.
- `errors` is an array of strings. Empty on success. On failure, the query still gets logged with whatever did succeed plus the error messages, even though the API response to the client is a clean error.
- Log file naming: `logs/queries_YYYY-MM-DD.log` — one file per day.
- No log rotation or cleanup. Acceptable for a project of this scope.

---

## 6. Error Handling Strategy

### 6.1 Failure Modes

| What fails | Cause | Impact |
|---|---|---|
| **ChromaDB** | Corrupted data, missing volume, embedding failure | Blocks retrieval and RAG answer |
| **Groq API** | Rate limiting (30 req/min), timeout, model overloaded | Blocks RAG answer, non-RAG answer, and/or LLM prediction |
| **ML model** | Missing `model.pkl`, corrupted file, feature extraction edge case | Blocks ML prediction |
| **Bad input** | Empty string, too long, non-text | Blocks everything |

### 6.2 Handling Rules

- **All-or-nothing response.** If any service fails, the entire `/query` request fails with an error response. No partial results. This avoids frontend complexity for handling missing fields.
- **Groq: retry once** with a 2-second delay. If it fails again, return 503. Don't retry more than once.
- **ML model: no retry.** It's local — if it fails, it's a bug, not a transient issue. Return 500.
- **ChromaDB: no retry.** Same reasoning — local, deterministic. Return 503.
- **Bad input: Pydantic validation.** `text` must be a non-empty string, max 1000 characters. Pydantic returns 422 automatically.
- **Log everything.** Even on failure, log the query, what succeeded, and the error. This is critical for debugging.

### 6.3 Error Response Shape

```json
{
  "error": "Groq API rate limited — retry after 30s",
  "status_code": 503
}
```

Status codes:

- **422** — bad input (Pydantic handles automatically)
- **500** — internal failure (model loading, feature extraction)
- **503** — external dependency unavailable (ChromaDB, Groq)

### 6.4 What We Are NOT Doing

No circuit breakers, no exponential backoff, no fallback responses, no graceful degradation. Document in the README that a production system would add these.

---

## 7. Shared Code Strategy

### 7.1 The Problem

`features.py` — the feature extraction function — must produce identical output in two places:

1. In the notebook during training (applied across 20k tweets to build the training DataFrame)
2. In the backend at inference time (called when a new query hits `/predict/ml`)

If these diverge, the model receives features computed differently from training. Predictions break silently.

### 7.2 The Solution

Write `features.py` once as a standalone module. It contains:

- `URGENCY_KEYWORDS` — the set of urgency keywords
- `NEGATIVE_KEYWORDS` — the set of negative keywords
- `extract_features(text) -> dict` — the function that computes all 9 features

During development:

1. Create `features.py` in the project root or notebook directory.
2. Import it in the notebook: `from features import extract_features`
3. Copy it into `backend/services/features.py` when building the backend.
4. Import it in the backend: `from services.features import extract_features`

It's a one-time copy, not a live link. Drift risk is negligible given the compressed timeline. In a production codebase, this would be a shared Python package — note this in the README.

### 7.3 Dependencies

`features.py` depends on `vaderSentiment` for the sentiment score. This must be in both the notebook environment and the backend's `requirements.txt`.

---

## 8. Backend Code Structure

```
backend/
├── Dockerfile
├── requirements.txt
├── main.py                  ← FastAPI app, mounts routers
├── routers/
│   ├── query.py             ← POST /query (orchestrator)
│   ├── retrieve.py          ← POST /retrieve
│   ├── generate.py          ← POST /generate/rag, POST /generate/no-rag
│   ├── predict.py           ← POST /predict/ml, POST /predict/llm
│   └── health.py            ← GET /health
├── services/
│   ├── retrieval.py         ← ChromaDB query logic
│   ├── llm.py               ← Groq API calls (all three prompts)
│   ├── ml_model.py          ← Load model.pkl, run predict
│   └── features.py          ← Shared feature extraction (copied from notebook)
├── schemas/
│   └── models.py            ← Pydantic request/response schemas
├── utils/
│   └── logger.py            ← JSONL query logging
├── ml/
│   └── model.pkl            ← Trained classifier
└── chroma_data/             ← ChromaDB persistent directory (volume-mounted)
```

No endpoint calls another endpoint. Routers call services. Services are standalone.

---

## 9. Frontend Components

```
frontend/
├── Dockerfile
├── package.json
└── src/
    ├── App.jsx              ← Single page, one fetch call to /query
    └── components/
        ├── QueryInput.jsx   ← Text box + submit button
        ├── AnswerPanel.jsx  ← RAG answer (primary) + non-RAG answer (secondary)
        ├── SourcePanel.jsx  ← Retrieved tickets with similarity scores
        └── ComparisonTable.jsx ← ML vs LLM: label, confidence, latency, cost
```

No routing library, no state management library. Just `useState` and one `fetch` call to `/query`.

---

## 10. Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - chroma_data:/app/chroma_data
      - logs:/app/logs
    env_file: .env

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  chroma_data:
  logs:

networks:
  default:
    name: dia-network
```

Two services. ChromaDB runs in-process inside `backend` — no third container. Justified in README as a deliberate simplicity tradeoff: acceptable for this scale, would use a dedicated vector DB service in production.

Named volumes for `chroma_data` and `logs` so data survives container restarts.

---

## 11. Environment Variables

`.env.example`:

```
GROQ_API_KEY=your-groq-api-key-here
GROQ_MODEL=openai/gpt-oss-20b
CHROMA_DATA_DIR=/app/chroma_data
LOG_DIR=/app/logs
TOP_K_DEFAULT=3
```

Never hardcode keys. `.env` is in `.gitignore`.

---

## 12. Deliverables Checklist

- [ ] `notebook.ipynb` — EDA, labeling logic, feature engineering, model comparison
- [ ] `backend/` — FastAPI with separated routers, schemas, services
- [ ] `frontend/` — React app with input, answers, sources, comparison
- [ ] `docker-compose.yml` — two services, named volumes, shared network
- [ ] `Dockerfile` in backend/ and frontend/
- [ ] `.env.example` — all variables with dummy values
- [ ] `.gitignore` — excludes `.env`, `venv/`, `__pycache__/`, `node_modules/`
- [ ] `README.md` — how to run, architecture, design decisions, known limitations, deployment recommendation
- [ ] `logs/` — captured via volume, JSONL format
- [ ] `features.py` — shared feature extraction, present in both notebook context and backend/services/
