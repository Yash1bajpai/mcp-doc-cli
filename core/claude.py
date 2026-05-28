from openai import OpenAI
from anthropic.types import Message
import anthropic


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
            if isinstance(message, Message)
            else message,
        }
        messages.append(user_message)

    def add_assistant_message(self, messages: list, message):
        assistant_message = {
            "role": "assistant",
            "content": message.content
            if isinstance(message, Message)
            else message,
        }
        messages.append(assistant_message)

    def text_from_message(self, message) -> str:
        if hasattr(message, "choices"):
            return message.choices[0].message.content or ""
        return "\n".join(
            [block.text for block in message.content if block.type == "text"]
        )

    def chat(
        self,
        messages,
        system=None,
        temperature=1.0,
        stop_sequences=[],
        tools=None,
        thinking=False,
        thinking_budget=1024,
    ):
        openai_messages = []

        if system:
            openai_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_result":
                            text_parts.append(str(block.get("content", "")))
                        elif block.get("type") == "tool_use":
                            text_parts.append(f"[Tool call: {block.get('name')}]")
                    elif hasattr(block, "type"):
                        if block.type == "text":
                            text_parts.append(block.text)
                        elif block.type == "tool_result":
                            text_parts.append(str(getattr(block, "content", "")))
                content = " ".join(text_parts)

            openai_messages.append({"role": role, "content": content})

        params = {
            "model": self.model,
            "max_tokens": 8000,
            "messages": openai_messages,
            "temperature": temperature,
        }

        if stop_sequences:
            params["stop"] = stop_sequences

        import time
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(**params)
                response.stop_reason = "end_turn"
                return response
            except Exception as e:
                if "429" in str(e) and attempt < 2:
                    print(f"Rate limited, retrying in 5s... ({attempt+1}/3)")
                    time.sleep(5)
                else:
                    raise
