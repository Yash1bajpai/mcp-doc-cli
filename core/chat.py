import json
from core.claude import Claude
from mcp_client import MCPClient
from core.tools import ToolManager

MAX_TOOL_ROUNDS = 8


class Chat:
    def __init__(self, claude_service: Claude, clients: dict[str, MCPClient]):
        self.claude_service: Claude = claude_service
        self.clients: dict[str, MCPClient] = clients
        self.messages: list[dict] = []

    async def _process_query(self, query: str):
        self.messages.append({"role": "user", "content": query})

    async def run(self, query: str) -> str:
        await self._process_query(query)
        tools = await ToolManager.get_all_tools(self.clients)

        final_text = ""
        for _ in range(MAX_TOOL_ROUNDS):
            response = self.claude_service.chat(
                messages=self.messages, tools=tools
            )
            tool_calls = self.claude_service.tool_calls_from_message(response)
            final_text = self.claude_service.text_from_message(response)

            if not tool_calls:
                self.messages.append(
                    {"role": "assistant", "content": final_text}
                )
                return final_text

            self.messages.append(
                {
                    "role": "assistant",
                    "content": final_text or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments or "{}",
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            )
            results = await ToolManager.execute_tool_calls(
                self.clients, tool_calls
            )
            self.messages.extend(results)

        final_text = final_text or "Stopped: too many tool-call rounds."
        self.messages.append({"role": "assistant", "content": final_text})
        return final_text
