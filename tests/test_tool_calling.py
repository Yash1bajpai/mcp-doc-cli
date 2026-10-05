import json
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from core.chat import Chat
from core.cli_chat import CliChat
from core.claude import Claude
from mcp_client import MCPClient

ROOT = Path(__file__).resolve().parent.parent


def make_client(tmp_path):
    return MCPClient(
        command=sys.executable,
        args=[str(ROOT / "mcp_server.py")],
        env={"DOCS_DIR": str(tmp_path), "PATH": ""},
    )


def tool_call(id, name, args):
    return NS(id=id, function=NS(name=name, arguments=json.dumps(args)))


class FakeLLM:
    """Scripted stand-in for the OpenRouter model."""

    def __init__(self, script):
        self.script = list(script)
        self.seen = []

    def chat(self, messages, tools=None, **_):
        self.seen.append((json.loads(json.dumps(messages, default=str)), tools))
        return self.script.pop(0)

    def text_from_message(self, m):
        return m["text"]

    def tool_calls_from_message(self, m):
        return m.get("calls", [])


async def test_tools_are_sent_and_edit_is_applied(tmp_path):
    async with make_client(tmp_path) as c:
        llm = FakeLLM([
            {"text": "", "calls": [tool_call("1", "edit_document",
                {"doc_id": "plan.md", "old_str": "outlines", "new_str": "describes"})]},
            {"text": "Done."},
        ])
        chat = Chat(llm, {"doc": c})
        assert await chat.run("edit plan.md") == "Done."
        names = {t["function"]["name"] for t in llm.seen[0][1]}
        assert names == {"read_doc_contents", "edit_document"}
        assert "describes" in (tmp_path / "plan.md").read_text()
        tool_msg = [m for m in chat.messages if m["role"] == "tool"][0]
        assert tool_msg["tool_call_id"] == "1" and "describes" in tool_msg["content"]


async def test_read_tool_and_unknown_tool_and_bad_args(tmp_path):
    async with make_client(tmp_path) as c:
        llm = FakeLLM([
            {"text": "", "calls": [
                tool_call("a", "read_doc_contents", {"doc_id": "spec.txt"}),
                tool_call("b", "nope", {}),
                tool_call("c", "read_doc_contents", {"doc_id": "missing.md"}),
            ]},
            {"text": "ok"},
        ])
        chat = Chat(llm, {"doc": c})
        await chat.run("go")
        by_id = {m["tool_call_id"]: m["content"] for m in chat.messages if m["role"] == "tool"}
        assert "specifications" in by_id["a"]
        assert by_id["b"].startswith("Error")
        assert by_id["c"].startswith("Error")


async def test_edit_with_missing_old_str_is_an_error(tmp_path):
    async with make_client(tmp_path) as c:
        out = await c.call_tool("edit_document",
            {"doc_id": "plan.md", "old_str": "zzz", "new_str": "y"})
        assert out.isError


async def test_round_limit_stops_loop(tmp_path):
    async with make_client(tmp_path) as c:
        call = {"text": "", "calls": [tool_call("x", "read_doc_contents", {"doc_id": "plan.md"})]}
        llm = FakeLLM([call] * 20)
        chat = Chat(llm, {"doc": c})
        assert "too many" in await chat.run("loop")


async def test_mention_injects_doc_and_resources(tmp_path):
    async with make_client(tmp_path) as c:
        llm = FakeLLM([{"text": "hi"}])
        chat = CliChat(doc_client=c, clients={"doc": c}, claude_service=llm)
        await chat.run("what is @report.pdf")
        sent = llm.seen[0][0][0]["content"]
        assert "condenser tower" in sent
        assert "docs://" not in sent
        assert sorted(await chat.list_docs_ids()) == sorted(
            ["deposition.md", "report.pdf", "financials.docx", "outlook.pdf", "plan.md", "spec.txt"])


async def test_prompts_listed_and_slash_command(tmp_path):
    async with make_client(tmp_path) as c:
        llm = FakeLLM([{"text": "summary"}])
        chat = CliChat(doc_client=c, clients={"doc": c}, claude_service=llm)
        assert {p.name for p in await chat.list_prompts()} == {"format", "summarize"}
        await chat.run("/summarize plan.md")
        assert "plan.md" in llm.seen[0][0][0]["content"]


def test_claude_passes_tools_to_openrouter(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    cl = Claude("m")
    captured = {}
    cl.client = NS(chat=NS(completions=NS(create=lambda **kw: captured.update(kw) or "R")))
    tools = [{"type": "function", "function": {"name": "t", "parameters": {}}}]
    assert cl.chat([{"role": "user", "content": "x"}], tools=tools) == "R"
    assert captured["tools"] == tools
    assert captured["messages"][0]["content"] == "x"
