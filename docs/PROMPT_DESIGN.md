# Prompt Design Spec

---

## 1. RAG Answer

**System prompt (static):**

```
You are a customer support assistant. You help support agents draft responses to customer complaints.

You will be given a new customer complaint and a set of similar past tickets with their resolutions. Use the patterns and resolution strategies from these past tickets to draft a helpful, professional response to the new complaint.

Do not copy past responses verbatim. Synthesize a new response appropriate to the specific complaint. Keep your response concise — 2-3 sentences max.
```

**User prompt (constructed at runtime):**

Built dynamically from the retrieval results. The function:

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

Example output the LLM would receive:

```
## Similar past tickets

Ticket 1 (similarity: 0.91):
Customer: "I was charged twice last month and support ignored me"
Resolution: "Sorry about that! Please DM us your account details and we'll issue a refund"

Ticket 2 (similarity: 0.85):
Customer: "Double charge on my account, been waiting 3 days"
Resolution: "We apologize for the delay. A refund has been initiated"

Ticket 3 (similarity: 0.79):
Customer: "Charged twice for my subscription, no response from support"
Resolution: "Please DM your email and we'll look into this right away"

## New complaint

"I've been charged twice this month and nobody is responding to my emails"

Draft a response to this complaint.
```

---

## 2. Non-RAG Answer

**System prompt (static):**

```
You are a customer support assistant. You help support agents draft responses to customer complaints.

Draft a helpful, professional response to the following complaint. Keep your response concise — 2-3 sentences max.
```

**User prompt (constructed at runtime):**

```python
def build_no_rag_user_prompt(query):
    return f"\"{query}\"\n\nDraft a response to this complaint."
```

Same system prompt minus the retrieval context instruction. The comparison between this and the RAG answer is the whole point — same model, same task, with and without retrieved context.

---

## 3. Zero-shot Priority Prediction

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

---

## Design Decisions

| Decision | Rationale |
|---|---|
| **2-3 sentence cap** | Support agents need quick drafts they can edit, not essays. Also keeps token usage and cost low. |
| **Labeling rule excluded from zero-shot prompt** | The ML model learns from rule-based labels. The LLM classifies from its own understanding of urgency. This is the comparison the brief asks for — a cheap model trained on your definition vs an expensive model using its own judgment. If you gave the LLM the same rule, you'd just be paying more for the same thing. |
| **Similarity scores included in RAG prompt** | Tells the LLM how much to trust each retrieved example. A 0.91 match is strong evidence; a 0.5 match is noise. The model can weight accordingly. |
| **Same system prompt structure for RAG and non-RAG** | Keeps the comparison fair. The only variable is whether retrieved context is present. |
