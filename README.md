# Igbo Archives Autonomous Books Agent

The **Books Agent** is an autonomous, scalable AI pipeline built entirely upon the Google GenAI ADK (`Agent`, `SequentialAgent`, `Context`) and the Model Context Protocol (MCP). It is engineered to research, fact-check, synthesize, and publish historical book recommendations to the Igbo Archives platform—with zero human intervention.

## The Story of the Pipeline

When a user requests a book recommendation (e.g., via the Telegram Bot), the command triggers the Master Orchestrator (`root_agent`). The Orchestrator acts as the central brain of a massive 9-agent ecosystem. Instead of forcing every research task into a rigid sequence, the Orchestrator dynamically utilizes specialized sub-agents as *tools*. It determines the required flow based on real-time findings ("the ifs").

Here is exactly how the pipeline evaluates and executes a request:

### Phase 1: Identification & Deduplication
1. **Identifier Agent**: The Orchestrator hands the raw user query to the `identifier_agent`. This agent executes `book_metadata_mcp.server.find_book` directly via native import, extracting the exact title, authors, and ISBNs. 
2. **Deduplication Check**: *IF* the book is found, the Orchestrator fires an HTTP JSON-RPC call (`check_duplicates`) via `mcp_client.py` to the Igbo Archives platform to pull the existing registry. *IF* the book is already in the archive, the Orchestrator halts execution immediately to prevent duplicates.

### Phase 2: Cover Art Acquisition & Visual Verification
3. **Cover Art Agent**: *IF* the book is new to the archive, the Orchestrator invokes the `cover_art_agent`. This intelligent agent handles the entire visual pipeline autonomously. It first downloads the default cover from the `raw_metadata` and runs an LLM vision pass (`gemma-4-31b-it`) to verify the text on the cover matches the expected title.
4. **Self-Correction (Fallback)**: If the vision model detects a mismatch (e.g., the cover image belongs to a completely different book), the agent *does not crash*. It seamlessly falls back to DuckDuckGo Image Search (`search_web_images`), scrapes alternative cover URLs, downloads them, and visually verifies them again until it establishes a confirmed match. It then securely locks the `verified_cover_url` into the state.

### Phase 3: The Exhaustive Research Pipeline (Mandatory)
Once the cover is verified, the Orchestrator triggers the `execute_books_pipeline`—a strict, deterministic sequence designed for absolutely rigorous, uncompromising research.
5. **Researcher Agent**: A RAG-powered agent that utilizes `duckduckgo_web_search` and targeted web scraping. It gathers deep historical context, cultural significance, and modern retail context, outputting exact text snippets without summarizing them, preserving source truth.

### Phase 4: Writer-Critic Validation & Publication
6. **Writer & Critic Loop**: Synthesizes the gathered research into purely factual, zero-fluff Editor.js blocks. An internal Critic ruthlessly validates the drafts against strict archival standards (no em-dashes, no AI filler, proper citations) to prevent hallucinations.
7. **Publisher Agent**: The final executioner. Only triggers if the Critic explicitly approves the draft. Pushes the fully approved Editor.js payload to the remote Igbo Archives database via MCP.

---

## Technical Infrastructure

- **No Paid Infrastructure**: To avoid reliance on costly and rate-limited APIs, all lookups are performed using lightweight local scrapers (`amazon_scraper.py`), DuckDuckGo Search (`ddgs`), and the `book-metadata-mcp` (Google Books/Open Library).
- **Google ADK & Resilience**: Model operations rely on `ResilientGemini`, a wrapper ensuring automatic fallbacks (e.g., from `gemma-4-31b-it` to `gemma-4-26b-a4b-it`) and exponential HTTP retries to gracefully handle 429 and 503 errors.
- **MCP Integration**: Unlike the `notes-agent` which strictly consumed HTTP APIs, the Books Agent demonstrates *hybrid MCP usage*. It natively imports logic from local standard I/O MCP servers while maintaining an asynchronous HTTP client for the remote Igbo Archives operations.

## Setup & Environment

To run this pipeline, you must have the following `.env` configuration:

```env
TELEGRAM_BOT_TOKEN=your_telegram_token
IGBO_ARCHIVES_TOKEN=ed9eabf6ff68dc1a32bff7b752224051cd27f15b
GOOGLE_BOOKS_API_KEY=optional_key
GOOGLE_API_KEY=your_gemini_api_key
```

Execute `uv run uvicorn app:app` or invoke the agent scripts directly.
