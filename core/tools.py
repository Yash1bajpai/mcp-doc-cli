import json
from typing import Optional
from mcp.types import TextContent
from mcp_client import MCPClient


class ToolManager:
    @classmethod
    async def get_all_tools(cls, clients: dict[str, MCPClient]) -> list[dict]:
        """MCP tools in OpenAI function-calling format."""
        tools = []
        for client in clients.values():
            for t in await client.list_tools():
                tools.append(
                    {
                        "type": "function",
                        "function": {
                            "name": t.name,
                            "description": t.description or "",
                            "parameters": t.inputSchema,
                        },
                    }
                )
        return tools

    @classmethod
    async def _find_client_with_tool(
        cls, clients: list[MCPClient], tool_name: str
    ) -> Optional[MCPClient]:
        for client in clients:
            tools = await client.list_tools()
            if any(t.name == tool_name for t in tools):
                return client
        return None

    @staticmethod
    def _result(tool_call_id: str, text: str) -> dict:
        return {"role": "tool", "tool_call_id": tool_call_id, "content": text}

    @classmethod
    async def execute_tool_calls(cls, clients: dict[str, MCPClient], tool_calls) -> list[dict]:
        """Run each model tool call via MCP; return OpenAI 'tool' messages."""
        results = []
        for tc in tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError as e:
                results.append(cls._result(tc.id, f"Error: invalid JSON arguments: {e}"))
                continue

            client = await cls._find_client_with_tool(list(clients.values()), name)
            if not client:
                results.append(cls._result(tc.id, f"Error: could not find tool '{name}'"))
                continue
            try:
                out = await client.call_tool(name, args)
                texts = [c.text for c in (out.content if out else []) if isinstance(c, TextContent)]
                text = "\n".join(texts)
                if out and out.isError:
                    text = f"Error: {text}"
                results.append(cls._result(tc.id, text))
            except Exception as e:
                results.append(cls._result(tc.id, f"Error executing tool '{name}': {e}"))
        return results
