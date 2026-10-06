import time

import openai
from openai import OpenAI


class LLMError(Exception):
    """A model/provider error with a message safe to show the user."""


class Claude:
    def __init__(self, model: str):
        import os
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    def add_user_message(self, messages: list, message):
        user_message = {
            "role": "user",
            "content": message.content
            if hasattr(message, "content")
            else message,
        }
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message):
        assistant_message = {
            "role": "assistant",
            "content": message.content
            if hasattr(message, "content")
            else message,
        }
        messages.append(assistant_message)

    def text_from_message(self, message) -> str:
        if hasattr(message, "choices"):
            return message.choices[0].message.content or ""
        return "\n".join(
            [block.text for block in message.content if block.type == "text"]
        )

    def tool_calls_from_message(self, message) -> list:
        if hasattr(message, "choices"):
            return message.choices[0].message.tool_calls or []
        return []

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=None,
        tools=None,
        **_ignored,
    ):
        """Send OpenAI-format messages (and optional OpenAI-format tools)."""
        openai_messages = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        openai_messages.extend(messages)

        params = {
            "model": self.model,
            "max_tokens": 8000,
            "messages": openai_messages,
            "temperature": temperature,
        }
        if stop_sequences:
            params["stop"] = stop_sequences
        if tools:
            params["tools"] = tools

        for attempt in range(3):
            try:
                return self.client.chat.completions.create(**params)
            except openai.RateLimitError as e:
                if attempt < 2:
                    print(f"Rate limited, retrying in 5s... ({attempt+1}/3)")
                    time.sleep(5)
                    continue
                raise LLMError(
                    f"The model '{self.model}' is rate limited right now "
                    "(free models share a provider limit). Wait a minute and "
                    "retry, or set a different CLAUDE_MODEL in .env."
                ) from e
            except openai.NotFoundError as e:
                raise LLMError(
                    f"The model '{self.model}' was not found or is no longer "
                    "available (OpenRouter returned 404). Pick another model "
                    "at openrouter.ai/models?max_price=0 and set CLAUDE_MODEL "
                    "in .env."
                ) from e
            except openai.AuthenticationError as e:
                raise LLMError(
                    "OpenRouter rejected the API key (401). Check "
                    "ANTHROPIC_API_KEY in .env."
                ) from e
