"""Real Claude class + real MCP server, against a local OpenAI-compatible fake API."""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from openai import OpenAI

from core.chat import Chat
from core.claude import Claude
from mcp_client import MCPClient

ROOT = Path(__file__).resolve().parent.parent
REQUESTS = []


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        REQUESTS.append(body)
        if body["messages"][-1]["role"] == "tool":
            msg = {"role": "assistant", "content": "Edited."}
            fin = "stop"
        else:
            msg = {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call_1", "type": "function",
                "function": {"name": "edit_document", "arguments": json.dumps(
                    {"doc_id": "spec.txt", "old_str": "define", "new_str": "specify"})}}]}
            fin = "tool_calls"
        out = json.dumps({"id": "x", "object": "chat.completion", "created": 0, "model": "m",
                          "choices": [{"index": 0, "message": msg, "finish_reason": fin}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)


async def test_full_loop_over_http(tmp_path, monkeypatch):
    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    cl = Claude("m")
    cl.client = OpenAI(base_url=f"http://127.0.0.1:{srv.server_port}/v1", api_key="k")
    async with MCPClient(sys.executable, [str(ROOT / "mcp_server.py")],
                         env={"DOCS_DIR": str(tmp_path)}) as c:
        out = await Chat(cl, {"d": c}).run("edit spec.txt")
    srv.shutdown()
    assert out == "Edited."
    assert {t["function"]["name"] for t in REQUESTS[0]["tools"]} == {"read_doc_contents", "edit_document"}
    assert "specify" in (tmp_path / "spec.txt").read_text()
