
# Igbo Archives Books Agent

[![AI-Powered](https://img.shields.io/badge/AI-Autonomous%20Agents-blueviolet)](https://google.github.io/google-adk/)
[![Powered by Gemma](https://img.shields.io/badge/Powered%20by-Gemma--4-blue)](https://deepmind.google/models/gemma/gemma-4/)
[![Book Metadata MCP](https://img.shields.io/badge/MCP-Book%20Metadata-green)](https://pypi.org/project/book-metadata-mcp/)

A specialized, fully autonomous AI pipeline designed for **Igbo Literary Ingestion**. This system expands the [Igbo Archives](https://igboarchives.com.ng) literary database by discovering culturally significant books, fetching exhaustive metadata, visually verifying cover art, and publishing high-density factual recommendations.

## 🏗️ Architecture
The system follows a clinical **Sequential Pipeline** leveraging Google ADK:

- **Discovery**: Scours digital libraries and the Igbo Archives API to identify significant literary works not yet present in the collection.
- **Metadata Analyst**: Fetches precise publication data, ISBNs, and descriptions using the [`book-metadata` MCP server](https://github.com/vetnet183/book-metadata-mcp).
- **Cover Auditor**: Downloads potential book covers and utilizes Gemini Vision to verify they match the metadata title and author before acceptance.
- **Researcher**: Gathers deep supplemental context, historical background, and biographical details about the author.
- **Writer & Critic Loop**: Synthesizes research into purely factual, zero-fluff recommendations formatted as Editor.js blocks. An internal critic validates drafts against strict archival standards.
- **Publisher**: Submits the final, validated book record and media path to the remote database.

## 🛠️ Tech Stack
- **Framework**: Google ADK
- **LLM Engine**: Google Gemma 4
- **Metadata**: [`book-metadata-mcp`](https://github.com/vetnet183/book-metadata-mcp) 

