"""
Thin Groq client.
"""

import logging
from functools import lru_cache
from groq import Groq
from pydantic import BaseModel

from app.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

# Model temperature (default = 1)
TEMPERATURE = 1


# NOTE: Use the cache to only create the client once
@lru_cache(maxsize=1)
def _get_groq_client():
    return Groq(api_key=GROQ_API_KEY)


def call(user_prompt: str,
         system_prompt: str,
         response_model: type[BaseModel] | None = None) -> str:
    """Call LLM with user prompt and system prompt. If response_model is provided, uses json_schema structured output."""
    client = _get_groq_client()

    logger.info("=== LLM PROMPT ===\nSYSTEM:\n%s\nUSER:\n%s", system_prompt, user_prompt)

    kwargs = dict(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=GROQ_MODEL,
        temperature=TEMPERATURE,
    )
    if response_model is not None:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": response_model.model_json_schema(),
            },
        }

    response = client.chat.completions.create(**kwargs)

    return response.choices[0].message.content
