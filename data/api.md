# API Contract

## Primary Endpoint

The frontend calls this single endpoint. The backend orchestrates all services internally and returns a unified response.

### `POST /query`

**Request:**

```json
{
  "text": "I've been charged twice and nobody is responding",
  "top_k": 5
}
```

**Response:**

```json
{
  "query": "I've been charged twice this month and nobody is responding to my emails",

  "sources": [
    {
      "ticket_id": "t_1042",
      "customer_text": "I was charged twice last month and support ignored me",
      "brand_reply": "Sorry about that! Please DM us your account details and we'll issue a refund",
      "similarity": 0.91
    },
    {
      "ticket_id": "t_2287",
      "customer_text": "Double charge on my account, been waiting 3 days",
      "brand_reply": "We apologize for the delay. A refund has been initiated",
      "similarity": 0.85
    },
    {
      "ticket_id": "t_3901",
      "customer_text": "Charged twice for my subscription, no response from support",
      "brand_reply": "Please DM your email and we'll look into this right away",
      "similarity": 0.79
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

---

## Debug / Testing Endpoints

These are for testing individual services in isolation. The frontend does not use them. All are self-contained — no endpoint calls another endpoint. They share underlying service functions at the code level.

The RAG-associated endpoints accept the `top_k` parameter in the request:
```
{
  "text": "I've been charged twice and nobody is responding",
  "top_k": 5
}
```  

Otherwise, we just submit the text in the request body: `{ "text": "..." }`.

### `POST /retrieve`

Returns similar past tickets from ChromaDB.

```json
{
  "sources": [
    {
      "ticket_id": "t_1042",
      "customer_text": "I was charged twice last month and support ignored me",
      "brand_reply": "Sorry about that! Please DM us your account details and we'll issue a refund",
      "similarity": 0.91
    }
  ],
  "latency_ms": 45
}
```

### `POST /generate/rag`

Retrieves similar tickets internally, then generates a response using them as context.

```json
{
  "response": "Based on similar cases...",
  "sources": [
    {
      "ticket_id": "t_1042",
      "customer_text": "...",
      "brand_reply": "...",
      "similarity": 0.91
    }
  ],
  "latency_ms": 1100,
  "cost_usd": 0.0008
}
```

### `POST /generate/no-rag`

Generates a response using the LLM alone, no retrieval.

```json
{
  "response": "I'm sorry to hear about the double charge...",
  "latency_ms": 780,
  "cost_usd": 0.0005
}
```

### `POST /predict/ml`

Extracts features from the text and runs the trained ML classifier.

```json
{
  "label": "urgent",
  "confidence": 0.87,
  "latency_ms": 1.8,
  "cost_usd": 0.0
}
```

### `POST /predict/llm`

Asks the LLM to classify priority using zero-shot prediction with structured output.

```json
{
  "label": "urgent",
  "confidence": 0.92,
  "latency_ms": 320,
  "cost_usd": 0.0003
}
```

### `GET /health`

```json
{
  "status": "ok"
}
```

---

## Error Response

Any endpoint returns this on failure:

```json
{
  "error": "LLM request timed out",
  "status_code": 503
}
```

---

## Design Decisions

| Decision | Detail |
|---|---|
| **Top-k** | Configurable via `top_k` request parameter, defaults to 3 |
| **Similarity** | Cosine similarity from ChromaDB, float 0–1 |
| **ML confidence** | `predict_proba` from scikit-learn — calibrated |
| **LLM confidence** | Self-reported via structured output — uncalibrated, documented as such |
| **Cost** | Calculated from Groq production pricing using token counts from the API response, not free tier ($0) pricing |
| **Latency** | Wall-clock `time.time()` around each service call, reported in milliseconds |
| **No nulls** | All fields always present. Failures return an error response, not partial data |
| **No endpoint-to-endpoint calls** | Routes share service functions at the code level. Retrieval logic lives in one place, used by `/retrieve`, `/generate/rag`, and `/query` |
