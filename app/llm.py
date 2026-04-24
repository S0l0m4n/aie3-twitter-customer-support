"""
Thin LLM client, supporting:
    * OpenAI
    * Groq
"""

import logging
import time

from functools import lru_cache
from groq import Groq
from openai import OpenAI
from pydantic import BaseModel

from app.config import (
    LLM_PROVIDER,
    GROQ_API_KEY, GROQ_MODEL,
    OPENAI_API_KEY, OPENAI_MODEL)

logger = logging.getLogger(__name__)

# Model temperature (default = 1)
TEMPERATURE = 1

LLM_MAX_RETRIES = 3
LLM_RETRY_DELAY = 1.0

# NOTE: Use the cache to only create the client once
@lru_cache(maxsize=1)
def _get_groq_client():
    return Groq(api_key=GROQ_API_KEY)

@lru_cache(maxsize=1)
def _get_openai_client():
    return OpenAI(api_key=OPENAI_API_KEY)

def _call_openai(user_prompt: str, system_prompt: str) -> str:
    """Call OpenAI API."""
    client = _get_openai_client()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=TEMPERATURE,
    )

    return response.choices[0].message.content

def _call_groq(user_prompt: str,
               system_prompt: str,
               response_model: type[BaseModel] | None = None) -> str:
    """Call Groq API."""
    client = _get_groq_client()

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

def call(user_prompt: str,
         system_prompt: str,
         response_model: type[BaseModel] | None = None) -> str:
    """
    Call LLM with user prompt and system prompt. If response_model is
    provided, uses json_schema structured output.

    Uses Gemini, OpenAI, or Azure OpenAI based on LLM_PROVIDER.
    Retries up to LLM_MAX_RETRIES times with exponential backoff.
    """
    logger.info("=== LLM PROMPT ===\nSYSTEM:\n%s\nUSER:\n%s", system_prompt, user_prompt)

    for attempt in range(LLM_MAX_RETRIES):
        try:
            if LLM_PROVIDER == "openai":
                # Response model not handled
                return _call_openai(user_prompt, system_prompt)
            elif LLM_PROVIDER == "groq":
                return _call_groq(user_prompt, system_prompt, response_model)
            else:
                raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")
        except Exception as e:
            logger.warning(
                "LLM call failed (attempt %d/%d): %s",
                attempt + 1,
                LLM_MAX_RETRIES,
                e,
            )
            if attempt == LLM_MAX_RETRIES - 1:
                raise
            time.sleep(LLM_RETRY_DELAY * (2 ** attempt))
