from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel, Field


load_dotenv(Path(__file__).with_name(".env"))


# This prompt tells the AI how to behave and when to call the weather tool.
SYSTEM_PROMPT = """You are a fast, accurate weather assistant.

Use chain-of-thought prompting internally:
1. Understand the user's exact weather requirement.
2. Extract the location, date/time intent, and requested weather fields.
3. Decide whether live weather data is needed.
4. If weather data is needed, call the get_weather tool before answering.
5. Check the tool result for resolved location, current conditions, and forecast.
6. Give the user only the final answer, not your private reasoning steps.

When the user asks for current weather, forecast, temperature, rain, wind, humidity,
or any weather-related condition for a place, you must call the get_weather tool.
If a location is missing, ask one short follow-up question.
Use the tool result as the source of truth. Be concise, practical, and mention when
weather data is approximate or unavailable.
Use ASCII characters only so the Windows CLI can print your answer reliably.
"""


# This schema tells the model that it can call our Python weather function.
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather and a short forecast for a city or place.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City, town, or place name, e.g. Balasore, London, New York.",
                }
            },
            "required": ["location"],
        },
    },
}


# This error is used when setup is missing, like GROQ_API_KEY.
class WeatherAgentError(RuntimeError):
    """Raised when the agent cannot complete a request."""


# This model checks the location coming from the AI tool call.
class WeatherToolInput(BaseModel):
    location: str = Field(min_length=1)


# This model keeps current weather data in a fixed structure.
class CurrentWeather(BaseModel):
    description: str | None = None
    temp_c: str | None = None
    feels_like_c: str | None = None
    humidity_percent: str | None = None
    wind_kmph: str | None = None
    wind_direction: str | None = None
    precip_mm: str | None = None
    observation_time: str | None = None


# This model keeps one forecast day in a fixed structure.
class ForecastDay(BaseModel):
    date: str | None = None
    avg_temp_c: str | None = None
    min_temp_c: str | None = None
    max_temp_c: str | None = None
    chance_of_rain: str | None = None


# This model is the final structured weather output for the AI.
class WeatherOutput(BaseModel):
    ok: bool
    requested_location: str | None = None
    resolved_location: str | None = None
    current: CurrentWeather | None = None
    forecast: list[ForecastDay] = Field(default_factory=list)
    source: str | None = None
    error: str | None = None


@dataclass
# This class handles the AI model, tool calling, and weather API.
class WeatherAgent:
    model: str = "openai/gpt-oss-120b"
    timeout_seconds: int = 8
    client: Groq = field(init=False)
    session: requests.Session = field(default_factory=requests.Session)

    # This function runs automatically when WeatherAgent is created.
    def __post_init__(self) -> None:
        if not os.getenv("GROQ_API_KEY"):
            raise WeatherAgentError(
                "GROQ_API_KEY is missing. Add it to weather_agent/.env or your shell environment."
            )

        self.client = Groq()
        self.session.headers.update(
            {"User-Agent": "weather-agent-cli/1.0 (https://wttr.in)"}
        )

    # This function sends the user's question to the AI and returns the answer.
    def ask(self, user_query: str) -> str:
        query = user_query.strip()
        if not query:
            return "Please ask a weather question."

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]

        first_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=[WEATHER_TOOL],
            tool_choice="auto",
            temperature=0.2,
            max_tokens=700,
        )

        assistant_message = first_response.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        if not tool_calls:
            return self._ascii_safe((assistant_message.content or "").strip())

        messages.append(self._assistant_tool_call_message(assistant_message))

        for tool_call in tool_calls:
            if tool_call.function.name != "get_weather":
                continue

            try:
                args = json.loads(tool_call.function.arguments or "{}")
                tool_input = WeatherToolInput.model_validate(args)
                result = self.get_weather(tool_input.location)
            except Exception as exc:
                result = {"ok": False, "error": str(exc)}

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "get_weather",
                    "content": json.dumps(result, ensure_ascii=True),
                }
            )

        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2,
            max_tokens=500,
        )
        return self._ascii_safe((final_response.choices[0].message.content or "").strip())

    # This function calls wttr.in API and gets real weather data.
    def get_weather(self, location: str) -> dict[str, Any]:
        if not location:
            return WeatherOutput(ok=False, error="Location is required.").model_dump(
                exclude_none=True
            )

        url = f"https://wttr.in/{quote(location)}"
        try:
            response = self.session.get(
                url,
                params={"format": "j1"},
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
        except requests.RequestException as exc:
            return WeatherOutput(
                ok=False,
                requested_location=location,
                error=f"Weather API request failed: {exc}",
            ).model_dump(exclude_none=True)
        except ValueError as exc:
            return WeatherOutput(
                ok=False,
                requested_location=location,
                error=f"Weather API returned invalid JSON: {exc}",
            ).model_dump(exclude_none=True)

        current = (payload.get("current_condition") or [{}])[0]
        nearest_area = (payload.get("nearest_area") or [{}])[0]
        weather_days = payload.get("weather") or []
        forecast: list[ForecastDay] = []

        for day in weather_days[:3]:
            forecast.append(
                ForecastDay(
                    date=day.get("date"),
                    avg_temp_c=day.get("avgtempC"),
                    min_temp_c=day.get("mintempC"),
                    max_temp_c=day.get("maxtempC"),
                    chance_of_rain=self._daily_chance(day, "chanceofrain"),
                )
            )

        weather_output = WeatherOutput(
            ok=True,
            requested_location=location,
            resolved_location=self._resolved_location(nearest_area),
            current=CurrentWeather(
                description=self._weather_description(current),
                temp_c=current.get("temp_C"),
                feels_like_c=current.get("FeelsLikeC"),
                humidity_percent=current.get("humidity"),
                wind_kmph=current.get("windspeedKmph"),
                wind_direction=current.get("winddir16Point"),
                precip_mm=current.get("precipMM"),
                observation_time=current.get("observation_time"),
            ),
            forecast=forecast,
            source="wttr.in",
        )
        return weather_output.model_dump(exclude_none=True)

    @staticmethod
    # This function formats the AI tool-call message for the next model call.
    def _assistant_tool_call_message(message: Any) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in (message.tool_calls or [])
            ],
        }

    @staticmethod
    # This function takes the weather description from the API response.
    def _weather_description(current: dict[str, Any]) -> str | None:
        descriptions = current.get("weatherDesc") or []
        if not descriptions:
            return None
        return descriptions[0].get("value")

    @staticmethod
    # This function formats the city, region, and country from the API response.
    def _resolved_location(nearest_area: dict[str, Any]) -> str | None:
        parts = []
        for key in ("areaName", "region", "country"):
            values = nearest_area.get(key) or []
            if values and values[0].get("value"):
                parts.append(values[0]["value"])
        return ", ".join(parts) if parts else None

    @staticmethod
    # This function finds the highest rain chance for one forecast day.
    def _daily_chance(day: dict[str, Any], key: str) -> str | None:
        chances = []
        for hour in day.get("hourly") or []:
            value = hour.get(key)
            if value and value.isdigit():
                chances.append(int(value))
        return str(max(chances)) if chances else None

    @staticmethod
    # This function cleans special symbols so Windows terminal can print nicely.
    def _ascii_safe(text: str) -> str:
        replacements = {
            "°": " deg",
            "≈": "about ",
            "\u00a0": " ",
            "\u202f": " ",
            "\u2010": "-",
            "\u2011": "-",
            "\u2012": "-",
            "–": "-",
            "—": "-",
            "‘": "'",
            "’": "'",
            "“": '"',
            "”": '"',
        }
        for source, target in replacements.items():
            text = text.replace(source, target)
        text = text.encode("ascii", errors="replace").decode("ascii")
        text = re.sub(r"\bdeg(?=[CF]\b)", "deg ", text)
        text = re.sub(r"(\d)\s+%", r"\1%", text)
        return "\n".join(re.sub(r"[ \t]{2,}", " ", line).strip() for line in text.splitlines())
