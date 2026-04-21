import asyncio
import re
import json
import logging
from SyncLLM import SyncLLM
from typing import Any, Coroutine


_JSON_BLOCK_RE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL | re.IGNORECASE)
_SMART_QUOTES = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'"})


def extract_json_snippet(text: str) -> str:
    """
    Extract the most likely JSON snippet from model output.

    Tries to handle Markdown code fences and extra commentary commonly added by LLMs.
    """
    if not text:
        raise ValueError("No text supplied for JSON extraction.")

    match = _JSON_BLOCK_RE.search(text)
    if match:
        candidate = match.group(1)
    else:
        # Fall back to slicing from the first opening brace/bracket to the last closing one.
        brace_idx = re.search(r"[{\[]", text)
        if not brace_idx:
            raise ValueError("No JSON object or array detected in model response.")
        opening = brace_idx.group()
        closing = "}" if opening == "{" else "]"
        start = brace_idx.start()
        end = text.rfind(closing)
        if end == -1:
            raise ValueError(
                "Could not find matching closing bracket for JSON payload."
            )
        candidate = text[start : end + 1]

    candidate = candidate.strip()
    if not candidate:
        raise ValueError("Extracted JSON snippet is empty.")
    return candidate


def _sanitise_json_like(payload: str) -> str:
    """
    Apply common fixes to LLM output that looks like JSON but is malformed.
    """
    out = payload.translate(_SMART_QUOTES)
    # Trailing commas before ] or }
    out = re.sub(r",(\s*[}\]])", r"\1", out)
    # Missing comma between adjacent structures (common LLM mistake)
    out = re.sub(r"}\s*{", "},{", out)
    out = re.sub(r"]\s*{", "],{", out)
    out = re.sub(r"}\s*\[", "},[", out)
    out = re.sub(r"]\s*\[", "],[", out)
    # Double commas -> single
    out = re.sub(r",\s*,", ",", out)
    return out


def parse_model_json(text: str, *, logger: logging.Logger | None = None) -> Any:
    """
    Convert Anthropic (or other LLM) JSON-ish output into Python objects.

    The function:
        1. Extracts a JSON snippet from the response (handling Markdown fences).
        2. Attempts a strict `json.loads`.
        3. Falls back to a lightly sanitised version that replaces “smart quotes”
           and strips trailing commas before closing braces/brackets.

    Parameters
    ----------
    text
        Raw LLM response text.
    logger
        Optional logger to emit warnings when sanitisation is required.

    Returns
    -------
    Any
        Parsed JSON payload (usually `dict` or `list`).

    Raises
    ------
    ValueError
        If no valid JSON can be parsed.
    """
    snippet = extract_json_snippet(text)

    def _loads(payload: str) -> Any:
        return json.loads(payload)

    try:
        return _loads(snippet)
    except json.JSONDecodeError:
        sanitised = _sanitise_json_like(snippet)
        try:
            if logger:
                logger.warning("Parsed JSON after sanitising LLM output.")
            return _loads(sanitised)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Unable to parse JSON from model response: {exc}"
            ) from exc

def parse_model_json_with_fallback(text: str, model: SyncLLM, resp_format: Any) -> Any:
    """
    Convert Anthropic (or other LLM) JSON-ish output into Python objects.
    """
    prompt = f"""
    Convert the following text into a JSON object. Return just the JSON, no other text.
    {text}
    """
    resp = model.call(prompt=prompt, resp_format=resp_format)
    return resp


async def batched_call(calls: list[Coroutine], max_concurrent: int) -> list[Any]:
    """Run async calls with a concurrency cap.

    Args:
        calls: List of coroutines to run.
        max_concurrent: Maximum number running at once.

    Returns:
        Results in the same order as the input calls.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _wrap(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(_wrap(c) for c in calls))
