from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


class SettingsError(RuntimeError):
    """Raised when required AI configuration is missing."""


@dataclass(frozen=True)
class Settings:
    provider: str
    model: str
    api_key: str
    primary_provider: str = ""
    fallback_model: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.6-flash"
    max_output_tokens: int = 3000
    temperature: float = 0.2

    @classmethod
    # Loads provider settings and API keys from .env or the shell.
    def load(cls) -> "Settings":
        load_dotenv(Path.cwd() / ".env")
        load_dotenv(Path(__file__).resolve().parents[1] / ".env")

        provider = os.getenv("AI_PROVIDER", "hybrid").strip().lower()
        model = os.getenv("AI_MODEL", "").strip()
        fallback_model = os.getenv("FALLBACK_MODEL", "").strip()
        gemini_model = os.getenv("GEMINI_MODEL", "").strip() or "gemini-3.6-flash"
        max_output_tokens = cls._read_int_env("MAX_OUTPUT_TOKENS", 3000)

        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY", "").strip()
            model = model or "openai/gpt-oss-120b"
        elif provider == "gemini":
            api_key = (
                os.getenv("GEMINI_API_KEY", "").strip()
                or os.getenv("GOOGLE_API_KEY", "").strip()
            )
            model = model or "gemini-3.6-flash"
        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "").strip()
            model = model or "gpt-4.1-mini"
        elif provider == "hybrid":
            gemini_api_key = (
                os.getenv("GEMINI_API_KEY", "").strip()
                or os.getenv("GOOGLE_API_KEY", "").strip()
            )
            openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
            groq_api_key = os.getenv("GROQ_API_KEY", "").strip()

            if openai_api_key:
                primary_provider = "openai"
                api_key = openai_api_key
                model = model or "gpt-4.1-mini"
            elif groq_api_key:
                primary_provider = "groq"
                api_key = groq_api_key
                model = model or "openai/gpt-oss-120b"
                fallback_model = fallback_model or "openai/gpt-oss-20b"
            else:
                raise SettingsError(
                    "Hybrid mode needs OPENAI_API_KEY or GROQ_API_KEY for the main model."
                )

            if not gemini_api_key:
                raise SettingsError("Hybrid mode needs GEMINI_API_KEY for the reviewer model.")

            return cls(
                provider=provider,
                model=model,
                api_key=api_key,
                primary_provider=primary_provider,
                fallback_model=fallback_model,
                gemini_api_key=gemini_api_key,
                gemini_model=gemini_model,
                max_output_tokens=max_output_tokens,
            )
        else:
            raise SettingsError("AI_PROVIDER must be 'hybrid', 'groq', 'gemini', or 'openai'.")

        if not api_key:
            env_names = {
                "groq": "GROQ_API_KEY",
                "gemini": "GEMINI_API_KEY",
                "openai": "OPENAI_API_KEY",
            }
            env_name = env_names[provider]
            raise SettingsError(f"{env_name} is missing. Add it to claude_code/.env or your shell.")

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            primary_provider=provider,
            fallback_model=fallback_model,
            gemini_model=gemini_model,
            max_output_tokens=max_output_tokens,
        )

    @staticmethod
    # Reads a number from the environment and falls back to a safe default.
    def _read_int_env(name: str, default: int) -> int:
        raw_value = os.getenv(name, "").strip()
        if not raw_value:
            return default
        try:
            return int(raw_value)
        except ValueError as exc:
            raise SettingsError(f"{name} must be a number.") from exc
