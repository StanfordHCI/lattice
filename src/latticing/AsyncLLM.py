"""
llm.py
------
This file contains utility functions for processing calls to LLMs.
"""

from pickle import TRUE
from openai import AsyncOpenAI
from google import genai
from anthropic import AsyncAnthropic
from together import AsyncTogether
from consts import MODEL_FAMILIES
import asyncio
import os
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from openai import APIError, RateLimitError
from anthropic import (
    AsyncAnthropic,
    APIError as AnthropicAPIError,
    RateLimitError as AnthropicRateLimitError,
    InternalServerError as AnthropicInternalServerError,
)
from typing import Any


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=6),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((AnthropicAPIError, AnthropicRateLimitError, AnthropicInternalServerError)),
)
async def call_anthropic(
    client: AsyncAnthropic,
    model: str,
    prompt: str,
    *,
    temperature: float = 1.0,
    max_tokens: int = 5000,
    resp_format: Any = None,
    is_verbose: bool = False,
) -> str:
    """
    Call Anthropic Messages API and return the text content of the first response block.

    Parameters
    ----------
    client
        An instance of `AsyncAnthropic` (already configured with API key).
    model
        Claude model identifier to call.
    prompt
        User prompt/message content.
    temperature
        Sampling temperature for Claude (default 1.0).
    max_tokens
        Maximum number of tokens to generate.
    system
        Optional system prompt to prepend.
    """
    if is_verbose:
        print(f"Calling Anthropic model {model} with prompt {prompt}")
    if not isinstance(client, AsyncAnthropic):
        raise TypeError("call_anthropic expects an AsyncAnthropic client.")

    messages = [{"role": "user", "content": prompt}]
    if resp_format:
        # Force structured output via tool use: the model must call the tool,
        # so its input is always validated against the Pydantic JSON schema.
        response = await client.messages.create(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
            tools=[{
                "name": "structured_output",
                "description": "Return the result in the required structured format.",
                "input_schema": resp_format.model_json_schema(),
            }],
            tool_choice={"type": "tool", "name": "structured_output"},
        )
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                return resp_format.model_validate(block.input)
        raise ValueError("Anthropic response did not include a tool_use block.")
    
    response = await client.messages.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )
    parts = [
        block.text
        for block in response.content
        if getattr(block, "type", None) == "text" and hasattr(block, "text")
    ]
    if not parts:
        raise ValueError("Anthropic response did not include any text content.")
    return "".join(parts)


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((APIError, RateLimitError)),
)
async def call_gpt(client, prompt, model, resp_format=None):
    try:
        if resp_format == None:
            resp = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "text"},
            )
            return resp.choices[0].message.content
        else:
            resp = await client.responses.parse(
                model=model,
                input=[{"role": "user", "content": prompt}],
                text_format=resp_format
            )

            return resp.output_parsed
    except Exception as e:
        print(e)
        raise

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((APIError, RateLimitError)),
)
async def call_gemini(client, prompt, model, resp_format=None):
    try:
        if resp_format == None:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text
        else:
            response = await client.aio.models.generate_content(
                model=model,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": resp_format.model_json_schema(),
                },
            )
            output = resp_format.model_validate_json(response.text)
            return output
    except Exception as e:
        print(e)
        raise

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type((APIError, RateLimitError)),
)
async def call_together(client, prompt, model, resp_format=None):
    model_name = MODEL_FAMILIES[model]["name"]
    try:
        if resp_format is None:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MODEL_FAMILIES[model]["context_window"],
            )
            return response.choices[0].message.content
        else:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                response_format={
                    "type": "json_schema",
                    "schema": resp_format.model_json_schema(),
                },
                max_tokens=MODEL_FAMILIES[model]["context_window"],
            )
            try:
                output = resp_format.model_validate_json(response.choices[0].message.content)
            except Exception as e:
                print(e)
                return response.choices[0].message.content
            return output
    except Exception as e:
        print(e)
        raise


class AsyncLLM:
    def __init__(self, name: str, api_key: str, provider: str | None = None):
        self.model_name = name
        if self.model_name not in MODEL_FAMILIES:
            raise ValueError(f"Model {self.model_name} not found")
        if provider is not None:
            self.provider = provider
        else:
            try:
                self.provider = MODEL_FAMILIES[self.model_name]["provider"]
            except Exception as e:
                raise ValueError(f"Provider for model {self.model_name} not found")
        self.client = self.setup_llm_fn(api_key)
        self._sem = asyncio.Semaphore(int(os.getenv("LLM_CONCURRENCY", "16")))

    def setup_llm_fn(self, api_key) -> AsyncOpenAI | AsyncAnthropic:
        if self.provider == "openai":
            llm_client = AsyncOpenAI(
                api_key=api_key,
            )
        elif self.provider == "anthropic":
            llm_client = AsyncAnthropic(
                api_key=api_key,
            )
        elif self.provider == "google":
            llm_client = genai.Client(api_key=api_key)
        elif self.provider == "together":
            llm_client = AsyncTogether(api_key=api_key)
        else:
            raise ValueError(f"Provider {self.provider} not supported")
        return llm_client

    async def call(self, prompt: str, resp_format=None):
        async with self._sem:
            if self.provider == "openai":
                return await call_gpt(
                    client=self.client,
                    prompt=prompt,
                    model=self.model_name,
                    resp_format=resp_format,
                )
            elif self.provider == "anthropic":
                return await call_anthropic(
                    client=self.client, 
                    prompt=prompt, 
                    model=self.model_name,
                    resp_format=resp_format,
                )
            elif self.provider == "google":
                return await call_gemini(
                    client=self.client,
                    prompt=prompt,
                    model=self.model_name,
                    resp_format=resp_format,
                )
            elif self.provider == "together":
                return await call_together(
                    client=self.client,
                    prompt=prompt,
                    model=self.model_name,
                    resp_format=resp_format,
                )
