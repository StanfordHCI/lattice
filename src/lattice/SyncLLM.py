"""
llm.py
------
This file contains utility functions for processing calls to LLMs.
"""

from openai import OpenAI
from google import genai
from anthropic import Anthropic
from together import Together
from consts import MODEL_FAMILIES
import os
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)
from openai import APIError, RateLimitError
from anthropic import (
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
def call_anthropic(
    client: Anthropic,
    model: str,
    prompt: str,
    *,
    temperature: float = 1.0,
    max_tokens: int = 5000,
    resp_format: Any = None,
) -> str:
    """
    Call Anthropic Messages API and return the text content of the first response block.

    Parameters
    ----------
    client
        An instance of `Anthropic` (already configured with API key).
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
    if not isinstance(client, Anthropic):
        raise TypeError("call_anthropic expects an Anthropic client.")

    messages = [{"role": "user", "content": prompt}]
    if resp_format:
        response = client.messages.create(
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

    response = client.messages.create(
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
def call_gpt(client, prompt, model, resp_format=None):
    try:
        if resp_format == None:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "text"},
            )
            return resp.choices[0].message.content
        else:
            resp = client.responses.parse(
                model=model,
                input=[{"role": "user", "content": prompt}],
                text_format=resp_format,
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
def call_gemini(client, prompt, model, resp_format=None):
    try:
        if resp_format == None:
            response =  client.models.generate_content(
                model=model,
                contents=prompt,
            )
            return response.text
        else:
            response =  client.models.generate_content(
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
def call_together(client, prompt, model, resp_format=None):
    model_name = MODEL_FAMILIES[model]["name"]
    try:
        if resp_format is None:
            response =  client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=MODEL_FAMILIES[model]["context_window"],
            )
            return response.choices[0].message.content
        else:
            response =  client.chat.completions.create(
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


class SyncLLM:
    def __init__(self, name: str, api_key: str, provider: str | None = None):
        self.model_name = name
        if provider is not None:
            self.provider = provider
        else:
            try:
                self.provider = MODEL_FAMILIES[self.model_name]["provider"]
            except Exception as e:
                raise ValueError(f"Provider for model {self.model_name} not found")
        self.client = self.setup_llm_fn(api_key)

    def setup_llm_fn(self, api_key) -> OpenAI | Anthropic:
        if self.provider == "openai":
            llm_client = OpenAI(
                api_key=api_key,
            )
        elif self.provider == "anthropic":
            llm_client = Anthropic(
                api_key=api_key,
            )
        elif self.provider == "google":
            llm_client = genai.Client(api_key=api_key)
        elif self.provider == "together":
            llm_client = Together(api_key=api_key)
        else:
            raise ValueError(f"Provider {self.provider} not supported")
        return llm_client

    def call(self, prompt: str, resp_format=None):
        if self.provider == "openai":
            return call_gpt(
                client=self.client,
                prompt=prompt,
                model=self.model_name,
                resp_format=resp_format,
            )
        elif self.provider == "anthropic":
            return call_anthropic(
                client=self.client, 
                prompt=prompt, 
                model=self.model_name,
                resp_format=resp_format,
            )
        elif self.provider == "google":
            return call_gemini(
                client=self.client,
                prompt=prompt,
                model=self.model_name,
                resp_format=resp_format,
            )
        elif self.provider == "together":
            return call_together(
                client=self.client,
                prompt=prompt,
                model=self.model_name,
                resp_format=resp_format,
            )
