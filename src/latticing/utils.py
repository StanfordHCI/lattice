import asyncio
import re
import json
import logging
from SyncLLM import SyncLLM
from typing import Any, Coroutine

logger = logging.getLogger(__name__)


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


def _process_json_chars(payload: str) -> str:
    """Single-pass fix: escape literal control chars inside strings and strip // and /* */ comments outside strings."""
    result = []
    in_string = False
    escape_next = False
    i = 0
    n = len(payload)
    while i < n:
        ch = payload[i]
        if escape_next:
            result.append(ch)
            escape_next = False
            i += 1
        elif in_string:
            if ch == '\\':
                result.append(ch)
                escape_next = True
                i += 1
            elif ch == '"':
                in_string = False
                result.append(ch)
                i += 1
            elif ch == '\n':
                result.append('\\n')
                i += 1
            elif ch == '\r':
                result.append('\\r')
                i += 1
            elif ch == '\t':
                result.append('\\t')
                i += 1
            else:
                result.append(ch)
                i += 1
        else:
            # Outside a string
            if ch == '"':
                in_string = True
                result.append(ch)
                i += 1
            elif ch == '/' and i + 1 < n and payload[i + 1] == '/':
                # Line comment — skip to end of line
                while i < n and payload[i] != '\n':
                    i += 1
            elif ch == '/' and i + 1 < n and payload[i + 1] == '*':
                # Block comment — skip to */
                i += 2
                while i < n - 1:
                    if payload[i] == '*' and payload[i + 1] == '/':
                        i += 2
                        break
                    i += 1
            else:
                result.append(ch)
                i += 1
    return ''.join(result)


def _sanitise_json_like(payload: str) -> str:
    """
    Apply common fixes to LLM output that looks like JSON but is malformed.
    """
    out = payload.translate(_SMART_QUOTES)
    # Strip // and /* */ comments; escape literal control chars inside strings
    out = _process_json_chars(out)
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
        pass

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
    Re-format malformed LLM JSON output by asking the format model to produce
    a valid response conforming to resp_format's schema.

    Extracts just the JSON portion from the raw text before sending to the model
    to avoid overloading it with surrounding commentary.
    """
    try:
        snippet = extract_json_snippet(text)
    except ValueError:
        snippet = text

    # Limit the snippet to avoid overflowing the model's useful context
    MAX_CHARS = 12_000
    if len(snippet) > MAX_CHARS:
        snippet = snippet[:MAX_CHARS]

    schema = resp_format.model_json_schema() if hasattr(resp_format, 'model_json_schema') else {}
    prompt = (
        "The following is malformed JSON. Fix it so it is valid and matches the schema below. "
        "Return ONLY the corrected JSON object.\n\n"
        f"Schema:\n{json.dumps(schema, indent=2)}\n\n"
        f"Malformed JSON:\n{snippet}"
    )
    resp = model.call(prompt=prompt, resp_format=resp_format)
    return resp


async def batched_call(
    calls: list[Coroutine],
    max_concurrent: int,
    *,
    return_exceptions: bool = False,
    progress=None,
) -> list[Any]:
    """Run async calls with a concurrency cap.

    Args:
        calls: List of coroutines to run.
        max_concurrent: Maximum number running at once.
        return_exceptions: When True, exceptions from individual calls are
            returned in-place as values (same semantics as
            ``asyncio.gather(return_exceptions=True)``) and a warning is logged
            for each failure.  When False (default), the first exception is
            re-raised after all calls complete so callers receive a clean error.
        progress: Optional tqdm progress bar. Incremented by 1 after each
            call completes (whether it succeeds or fails).

    Returns:
        Results in the same order as the input calls.  When
        *return_exceptions* is True, failed positions hold the caught
        ``BaseException`` instance instead of a result value.
    """
    semaphore = asyncio.Semaphore(max_concurrent)

    async def _wrap(coro):
        async with semaphore:
            try:
                return await coro
            finally:
                if progress is not None:
                    progress.update(1)

    results = await asyncio.gather(*(_wrap(c) for c in calls), return_exceptions=True)

    failures = [(i, r) for i, r in enumerate(results) if isinstance(r, BaseException)]
    for i, exc in failures:
        logger.warning("batched_call: item %d failed — %s: %s", i, type(exc).__name__, exc)

    if not return_exceptions and failures:
        raise failures[0][1]

    return list(results)
