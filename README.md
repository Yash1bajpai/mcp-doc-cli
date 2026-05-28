# FRIDAY - Terminal AI Assistant

A fast, asynchronous command-line interface (CLI) for interacting with Large Language Models directly from the terminal. 

Currently powered by the OpenRouter API (utilizing the OpenAI Python SDK architecture), this project is built with a highly modular structure. The core design philosophy prioritizes flexibility, allowing seamless switching between cloud-based models (Llama-3, Gemma, Mistral) and serving as the foundational client for an eventual transition to secure, offline edge computing using local quantized models (GGUF/llama.cpp).

## Features

* **Interactive CLI Interface:** Fluid, continuous chat loop directly in the terminal.
* **Asynchronous Execution:** Built with Python's `asyncio` for non-blocking I/O operations and fast response rendering.
* **Universal API Routing:** Uses OpenRouter to instantly hot-swap between top-tier free and paid open-source models without changing the core codebase.
* **Modular Architecture:** Clean separation of concerns between the CLI engine (`cli.py`), chat logic (`chat.py`), and the API service wrapper (`claude.py`).
* **Privacy-Ready:** Structurally prepared to easily detach from cloud APIs and connect to local inference servers for 100% offline, private data handling.

## Prerequisites

* Python 3.10+ (Tested on Python 3.13)
* An active [OpenRouter](https://openrouter.ai/) account and API Key.

## Installation

1. **Navigate to the project directory:**
   ```bash
   cd cli_project_COMPLETE
