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
         response_model: type[BaseModel]) -> BaseModel:
    """Call LLM with user prompt and system prompt."""
    client = _get_groq_client()

    logger.info("=== LLM PROMPT ===\nSYSTEM:\n%s\nUSER:\n%s", system_prompt, user_prompt)

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=GROQ_MODEL,
        temperature=TEMPERATURE,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "schema": response_model.model_json_schema(),
            },
        },
    )

    return response.choices[0].message.content
