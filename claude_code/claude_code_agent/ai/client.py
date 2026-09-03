from __future__ import annotations

import time
import warnings
from typing import Any

from google import genai
from google.genai import types
from groq import Groq
from openai import OpenAI

from ..config import Settings


class AIClient:
    # Creates the right AI clients based on the selected provider.
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        provider = settings.primary_provider or settings.provider
        if provider == "groq":
            self.client: Any = Groq(api_key=settings.api_key)
        elif provider == "gemini":
            self.client = genai.Client(api_key=settings.api_key)
        else:
            self.client = OpenAI(api_key=settings.api_key)

        self.gemini_client = None
        if settings.provider == "hybrid":
            self.gemini_client = genai.Client(api_key=settings.gemini_api_key)

    # Gets the next JSON action from the selected AI setup.
    def complete(self, messages: list[dict[str, str]]) -> str:
        if self.settings.provider == "hybrid":
            draft = self._complete_primary(messages)
            return self._review_with_gemini(messages, draft)

        return self._complete_primary(messages)

    # Sends messages to the main model, such as OpenAI or Groq.
    def _complete_primary(self, messages: list[dict[str, str]]) -> str:
        if self.settings.provider == "gemini":
            return self._complete_gemini(messages)

        response = self._chat_completion_with_retry(messages)
        content = response.choices[0].message.content
        if not content:
            reasoning = getattr(response.choices[0].message, "reasoning", None)
            detail = f" Reasoning field: {reasoning[:300]}" if reasoning else ""
            raise RuntimeError("AI returned an empty response." + detail)
        return content.strip()

    # Retries temporary provider errors and switches to a fallback model when available.
    def _chat_completion_with_retry(self, messages: list[dict[str, str]]) -> Any:
        models = [self.settings.model]
        if self.settings.fallback_model and self.settings.fallback_model not in models:
            models.append(self.settings.fallback_model)

        last_error: Exception | None = None
        for model in models:
            for strict_json in (True, False):
                for attempt in range(3):
                    try:
                        return self._create_chat_completion(
                            model=model,
                            messages=messages,
                            strict_json=strict_json,
                        )
                    except Exception as exc:
                        last_error = exc
                        if self._is_json_mode_error(exc) and strict_json:
                            break
                        if not self._is_temporary_provider_error(exc):
                            raise
                        time.sleep(2 * (attempt + 1))

        raise RuntimeError(
            "The AI provider is temporarily unavailable after retries. "
            "Try again in a few minutes or set FALLBACK_MODEL to another model."
        ) from last_error

    # Makes one chat request, with strict JSON mode only when the provider accepts it.
    def _create_chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        strict_json: bool,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": self.settings.temperature,
            "max_tokens": self.settings.max_output_tokens,
        }
        if strict_json:
            kwargs["response_format"] = {"type": "json_object"}
        return self.client.chat.completions.create(**kwargs)

    # Sends messages to Gemini and asks it to return JSON.
    def _complete_gemini(self, messages: list[dict[str, str]]) -> str:
        client = self.gemini_client or self.client
        system_instruction = "\n\n".join(
            message["content"] for message in messages if message["role"] == "system"
        )
        contents = "\n\n".join(
            f"{message['role'].upper()}:\n{message['content']}"
            for message in messages
            if message["role"] != "system"
        )
        response = self._gemini_generate_with_retry(
            client=client,
            model=self.settings.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=self.settings.temperature,
                max_output_tokens=self.settings.max_output_tokens,
                response_mime_type="application/json",
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")
        return response.text.strip()

    # Lets Gemini review the main model's action before any tool is run.
    def _review_with_gemini(self, messages: list[dict[str, str]], draft: str) -> str:
        if self.gemini_client is None:
            raise RuntimeError("Hybrid mode is missing the Gemini client.")

        context = "\n\n".join(
            f"{message['role'].upper()}:\n{message['content']}" for message in messages[-4:]
        )
        review_prompt = (
            "You are the JSON action reviewer for a coding agent.\n"
            "Return exactly one valid JSON action object with keys action and args.\n"
            "If the draft is valid and safe, return it unchanged.\n"
            "If the draft is invalid JSON, unsafe, or does not follow the available action protocol, "
            "repair it into the safest useful next action.\n\n"
            f"Recent conversation:\n{context}\n\n"
            f"Draft action:\n{draft}"
        )
        response = self._gemini_generate_with_retry(
            client=self.gemini_client,
            model=self.settings.gemini_model,
            contents=review_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=self.settings.max_output_tokens,
                response_mime_type="application/json",
            ),
        )
        if not response.text:
            return draft
        return response.text.strip()

    # Retries Gemini when the free API is busy or rate limited.
    def _gemini_generate_with_retry(self, client: Any, **kwargs: Any) -> Any:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore",
                        message="Direct use of automatic function calling.*",
                    )
                    return client.models.generate_content(**kwargs)
            except Exception as exc:
                last_error = exc
                if not self._is_temporary_provider_error(exc):
                    raise
                time.sleep(2 * (attempt + 1))
        raise RuntimeError(
            "Gemini is temporarily unavailable after retries. Try again in a few minutes."
        ) from last_error

    @staticmethod
    # Checks if an API error looks temporary, like 503 busy or 429 rate limit.
    def _is_temporary_provider_error(exc: Exception) -> bool:
        text = str(exc).lower()
        temporary_markers = [
            "429",
            "503",
            "unavailable",
            "rate limit",
            "too many requests",
            "temporarily",
            "high demand",
            "resource_exhausted",
        ]
        return any(marker in text for marker in temporary_markers)

    @staticmethod
    # Checks if provider-side JSON mode failed before returning a response.
    def _is_json_mode_error(exc: Exception) -> bool:
        text = str(exc).lower()
        json_markers = [
            "json_validate_failed",
            "failed to validate json",
            "failed_generation",
        ]
        return any(marker in text for marker in json_markers)
