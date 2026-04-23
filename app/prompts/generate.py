# ============================================================
# System prompts to the LLM for generating a response to a customer support
# query.
# ============================================================

from app.schemas import Source

GENERATE_NO_RAG_PROMPT = """\
You are a customer support assistant. You help support agents draft responses to customer complaints.

Draft a helpful, professional response to the following complaint. Keep your response concise — 2-3 sentences max.
"""

GENERATE_RAG_PROMPT = """\
You are a customer support assistant. You help support agents draft responses to customer complaints.

You will be given a new customer complaint and a set of similar past tickets with their resolutions. Use the patterns and resolution strategies from these past tickets to draft a helpful, professional response to the new complaint.

Do not copy past responses verbatim. Synthesize a new response appropriate to the specific complaint. Do not reference unverified links in your response. Keep your response concise — 2-3 sentences max.
"""


def build_rag_user_prompt(query: str, sources: list[Source]) -> str:
    context = "## Similar past tickets\n\n"
    for i, source in enumerate(sources, 1):
        context += f"Ticket {i} (similarity: {source.similarity:.2f}):\n"
        context += f"Customer: \"{source.customer_text}\"\n"
        context += f"Resolution: \"{source.brand_reply}\"\n\n"
    context += "## New complaint\n\n"
    context += f"\"{query}\"\n\n"
    context += "Draft a response to this complaint."
    return context
