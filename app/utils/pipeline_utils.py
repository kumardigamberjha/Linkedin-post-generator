"""
Shared helpers: JSON extraction, LLM builder, and the validate-with-retry LLM caller.

LLM note
--------
Uses crewai.LLM whose .call() method is synchronous. The async retry helper below
runs llm.call inside asyncio.to_thread to avoid blocking the event loop.
"""

import asyncio
import json
import logging
import re
import unicodedata
import httpx

from pydantic import BaseModel

from app.core.config import get_settings
from app.services.llm import build_llm

logger = logging.getLogger(__name__)


class AgentFailedError(Exception):
    """Raised when an agent fails to produce schema-valid JSON after all retries."""


# ── Per-provider output-token ceilings ──────────────────────────────────────
_PROVIDER_MAX_TOKENS = {
    "ollama": 4096,  # reasoning models need space for think blocks
    "google": 1024,  # Gemini produces clean JSON — 1024 is ample for any agent
    "gemini": 1024,
}


def make_llm(provider: str, temperature: float, max_tokens: int = 4096):
    """Build a crewai.LLM for the given provider with fixed temperature and token ceiling."""
    settings = get_settings()
    llm = build_llm(provider, settings)
    # Normalise "ollama/model-name" → "ollama" so prefixed provider strings
    # still hit the correct cap entry in _PROVIDER_MAX_TOKENS.
    provider_key = (provider or "").lower().split("/")[0]
    cap = _PROVIDER_MAX_TOKENS.get(provider_key, max_tokens)
    # Gemini 3.x rejects a forced temperature — let it use the model default.
    is_gemini = provider_key in ("google", "gemini")
    try:
        if not is_gemini:
            llm.temperature = temperature
        llm.max_tokens = min(max_tokens, cap)
    except Exception:
        pass
    return llm


def make_fallback_llm(
    temperature: float, max_tokens: int = 4096, primary_provider: str = ""
):
    """Build an Ollama fallback LLM to use when the primary provider fails or hits rate limits."""
    settings = get_settings()
    llm = build_llm("ollama", settings)
    cap = _PROVIDER_MAX_TOKENS.get("ollama", max_tokens)
    try:
        llm.temperature = temperature
        llm.max_tokens = min(max_tokens, cap)
    except Exception:
        pass
    return llm


def _sanitize_control_chars(text: str) -> str:
    """Escape literal control characters inside JSON string literals.

    Local models (Ollama) often emit raw newlines/tabs inside JSON strings
    instead of the required \\n/\\t escape sequences, causing json.loads to
    raise 'Invalid control character'. This state-machine walks the JSON text
    and fixes only characters inside string values, leaving structural chars
    (braces, colons, commas) untouched.
    """
    result: list[str] = []
    in_string = False
    escape_next = False
    _ESC = {"\n": "\\n", "\r": "\\r", "\t": "\\t", "\b": "\\b", "\f": "\\f"}
    for ch in text:
        if escape_next:
            result.append(ch)
            escape_next = False
        elif ch == "\\" and in_string:
            result.append(ch)
            escape_next = True
        elif ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ord(ch) < 0x20:
            result.append(_ESC.get(ch, f"\\u{ord(ch):04x}"))
        else:
            result.append(ch)
    return "".join(result)


def extract_json(raw: str) -> dict:
    """
    Robustly extract a JSON object/array from LLM output that may contain:
      - Markdown fences (```json ... ```)
      - Surrounding prose
      - Trailing commas (a common small-model mistake)
      - Literal control characters inside string values (local model quirk)
    """
    if raw is None or str(raw).strip() == "":
        raise ValueError("No JSON found in LLM output: <empty>")

    text = str(raw)

    # Step 0: strip reasoning/thinking blocks emitted by models like Nemotron,
    # QwQ, DeepSeek-R1, etc. before any other processing.
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(
        r"<thinking>.*?</thinking>", "", text, flags=re.DOTALL | re.IGNORECASE
    )

    # Step 1: strip markdown fences
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text)

    # Step 2: find the outermost { ... } or [ ... ]
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in LLM output: {text[:200]!r}")

    candidate = match.group(0)

    # Step 2.5: fix literal control characters that local models emit inside strings
    candidate = _sanitize_control_chars(candidate)

    # Step 3: fix trailing commas (small models love these)
    candidate = re.sub(r",\s*}", "}", candidate)
    candidate = re.sub(r",\s*]", "]", candidate)

    data = json.loads(candidate)
    if isinstance(data, list):
        raise ValueError(
            f"Expected a JSON object but got an array. First items: {data[:3]}"
        )
    return data


def slugify(title: str) -> str:
    """URL-safe slug from a title."""
    title = (
        unicodedata.normalize("NFKD", title or "")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    title = title.lower().strip()
    title = re.sub(r"[^\w\s-]", "", title)
    title = re.sub(r"[\s_-]+", "-", title)
    title = re.sub(r"^-+|-+$", "", title)
    return title or "untitled-post"


def _invoke_llm(llm, prompt: str) -> str:
    """Synchronous single call into crewai.LLM. Returns the response text."""
    try:
        response = llm.call(prompt)
        logger.warning(f"Raw response type: {type(response)}, dir: {dir(response)}")

        if hasattr(response, "content"):
            res_str = response.content
        else:
            res_str = str(response)

        logger.warning(
            f"Extracted response string (first 100 chars): {res_str[:100]!r}"
        )
        return res_str
    except Exception:
        logger.exception("Exception in _invoke_llm")
        raise


# We no longer use a global rate limit flag because Gemini 503s are temporary.
# We want to keep retrying the primary API rather than falling back to a potentially broken local model.


async def check_gemini_health(provider: str) -> bool:
    """
    Perform a quick check on Gemini API health with a 2-second timeout.
    Returns True if healthy, False if rate-limited (429) or unavailable (503).
    """
    if not ("google" in provider.lower() or "gemini" in provider.lower()):
        return True

    settings = get_settings()
    if not settings.gemini_api_key:
        return False

    model = provider.split("/", 1)[1] if "/" in provider else "gemini-3.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}?key={settings.gemini_api_key}"
    try:
        async with httpx.AsyncClient() as client:
            # We use a GET request to the model info endpoint rather than inference.
            # This is extremely fast (< 500ms) and avoids generation timeouts.
            resp = await client.get(url, timeout=3.0)
            if resp.status_code in (429, 503):
                logger.warning("Gemini health check failed: HTTP %d", resp.status_code)
                return False
            return resp.status_code < 500
    except Exception as e:
        err_msg = str(e) or e.__class__.__name__
        logger.warning("Gemini health check request failed/timed out: %s", err_msg)
        return False


async def call_llm_with_retry(
    llm,
    prompt: str,
    schema_class: type[BaseModel],
    temperature: float,
    max_retries: int = 5,
    agent_name: str = "Agent",
    fallback_llm=None,
) -> BaseModel:
    """
    Call the LLM, extract JSON, and validate it against schema_class.
    Retries up to max_retries times on any failure.
    If fallback_llm is provided and all primary retries are exhausted,
    makes one attempt with the fallback before raising AgentFailedError.
    """
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            try:
                llm.temperature = temperature
            except Exception:
                pass
            raw = await asyncio.to_thread(_invoke_llm, llm, prompt)
            data = extract_json(raw)
            return schema_class(**data)
        except Exception as e:
            last_error = e
            logger.warning(
                "%s attempt %d/%d failed: %s", agent_name, attempt, max_retries, e
            )

            e_str = str(e).lower()
            if "503" in e_str or "unavailable" in e_str or "429" in e_str:
                logger.warning(
                    "%s hit 503/429. Sleeping for 5 seconds before retrying...",
                    agent_name,
                )
                await asyncio.sleep(5)
            elif attempt < max_retries:
                await asyncio.sleep(2)
            continue

    if fallback_llm is not None:
        logger.warning("%s primary exhausted — trying Ollama fallback.", agent_name)

        try:
            try:
                fallback_llm.temperature = temperature
            except Exception:
                pass
            raw = await asyncio.to_thread(_invoke_llm, fallback_llm, prompt)
            data = extract_json(raw)
            return schema_class(**data)
        except Exception as e:
            last_error = e
            logger.warning("%s fallback also failed: %s", agent_name, e)

    raise AgentFailedError(
        f"{agent_name} failed after {max_retries} attempts. Last error: {last_error}"
    )
