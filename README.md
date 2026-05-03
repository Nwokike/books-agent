# Igbo Archives Books Agent

[![AI-Powered](https://img.shields.io/badge/AI-Autonomous%20Agents-blueviolet)](https://google.github.io/google-adk/)
[![Powered by Gemma](https://img.shields.io/badge/Powered%20by-Gemma--4-blue)](https://deepmind.google/models/gemma/gemma-4/)

A specialized, fully autonomous AI pipeline designed for **Igbo Literary Ingestion**. This system expands the [Igbo Archives](https://igboarchives.com.ng) literary database by discovering culturally significant books, fetching exhaustive metadata, visually verifying cover art, and publishing high-density factual recommendations.

## 🏗️ Architecture
The system follows a clinical **Sequential Pipeline** leveraging Google ADK:

- **Discovery**: Scours digital libraries and the Igbo Archives API to identify significant literary works not yet present in the collection.
- **Metadata Analyst**: Fetches precise publication data, ISBNs, and descriptions using the `book-metadata` MCP server.
- **Cover Auditor**: Downloads potential book covers and utilizes Gemini Vision to verify they match the metadata title and author before acceptance.
- **Researcher**: Gathers deep supplemental context, historical background, and biographical details about the author.
- **Writer & Critic Loop**: Synthesizes research into purely factual, zero-fluff recommendations formatted as Editor.js blocks. An internal critic validates drafts against strict archival standards.
- **Publisher**: Submits the final, validated book record and media path to the remote database.

## 🛠️ Tech Stack
- **Framework**: Google ADK
- **LLM Engine**: Google Gemma 4 (`gemma-4-31b-it` / `gemma-4-26b-a4b-it`)
- **Metadata**: `book-metadata-mcp` (Google Books & Open Library)

## 🚀 Installation & Usage

### 1. Setup
```bash
git clone https://github.com/Nwokike/books-agent.git
cd books-agent
uv sync
```

### 2. Run the Agent
The app auto-detects its environment, running as a Telegram Polling Bot locally or a Webhook on Render.
```bash
# Start the Telegram Bot Interface
uv run python app.py
```
