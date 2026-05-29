# mcp-doc-cli

A command-line AI assistant built with **Model Context Protocol (MCP)** that can read, edit, and summarize documents — powered by any OpenRouter-compatible LLM (free tier supported).

Built as part of the [Anthropic Academy MCP Course](https://anthropic.skilljar.com/introduction-to-model-context-protocol).

---

## What it does

- Chat with an LLM directly from your terminal
- **@mention documents** to inject their content into context
- **MCP Tools** — AI can read and edit documents via tool calls
- **MCP Resources** — lists and fetches docs via URI (`docs://documents`)
- **MCP Prompts** — `/format` and `/summarize` slash commands with tab autocomplete
- Auto-retry on rate limit (429) with backoff
- Works with any OpenRouter free model — no paid API needed

---

## Architecture

```
main.py
├── MCPClient          # Spawns mcp_server.py as subprocess, handles tool/resource/prompt calls
├── Claude (core/)     # OpenRouter API wrapper (OpenAI-compatible)
├── CliChat (core/)    # Orchestrates @mentions, /commands, tool execution
└── CliApp  (core/)    # prompt-toolkit CLI with tab autocomplete
```

---

## Setup

### 1. Get a free API key

Sign up at [openrouter.ai](https://openrouter.ai) → Keys → Create Key (no credit card needed)

### 2. Clone and install

```bash
git clone https://github.com/Yash1bajpai/mcp-doc-cli
cd mcp-doc-cli
```

Install with `uv` (recommended):

```bash
pip install uv
uv sync
```

Or with pip:

```bash
pip install -r requirements.txt
```

### 3. Configure `.env`

```bash
cp .env.example .env
```

Edit `.env`:

```
CLAUDE_MODEL="moonshotai/kimi-k2.6:free"   # or any free model from openrouter.ai/models?max_price=0
ANTHROPIC_API_KEY="sk-or-your-key-here"
USE_UV=1
```

### 4. Run

```bash
uv run main.py
```

---

## Usage

### Basic chat
```
> what is the Model Context Protocol?
```

### @mention a document
```
> summarize @report.pdf
> what does @deposition.md say about Angela Smith?
```

### Slash commands (with tab autocomplete)
```
> /format deposition.md      # rewrites doc in Markdown
> /summarize financials.docx  # 2-3 line plain English summary
```

### Edit a document via natural language
```
> edit deposition.md and replace "Angela Smith" with "John Doe"
```

---

## Available Documents (default)

| ID | Description |
|----|-------------|
| `deposition.md` | Testimony of Angela Smith, P.E. |
| `report.pdf` | State of a 20m condenser tower |
| `financials.docx` | Project budget and expenditures |
| `outlook.pdf` | Projected future system performance |
| `plan.md` | Project implementation steps |
| `spec.txt` | Technical equipment requirements |

Add your own in `mcp_server.py` → `docs` dict.

---

## Tech Stack

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) — tools, resources, prompts
- [OpenAI Python SDK](https://github.com/openai/openai-python) — OpenRouter-compatible API calls
- [prompt-toolkit](https://github.com/prompt-toolkit/python-prompt-toolkit) — tab autocomplete, history
- [uv](https://github.com/astral-sh/uv) — fast dependency management

---

## Related

- [Anthropic Academy — MCP Course](https://anthropic.skilljar.com/introduction-to-model-context-protocol)
- [MCP Specification](https://modelcontextprotocol.io)
