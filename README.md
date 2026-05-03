# BooksAgent

BooksAgent is a fully autonomous research and publication system built to discover, research, and archive culturally significant literature into the Igbo Archives database without any human intervention.

## Architecture & Workflow

The platform operates using a deterministic multi-agent pipeline managed by an **Orchestrator**. The entire ingestion cycle runs autonomously:

1. **Discovery Agent**: Acts as an elite literary scout.
   - It is equipped with MCP tools (`mcp_find_book`, `mcp_search_book`) to find books.
   - It checks the Igbo Archives database to ensure the book isn't already archived.
   - If MCP tools don't return satisfactory results, it autonomously falls back to a DuckDuckGo web search to find lists of books.
   - **Output:** Returns exactly the title and author of a novel book.

2. **Metadata Agent**: Acts as a master archivist.
   - Equipped with all six `book-metadata` MCP tools (`find_book`, `search_book`, `get_metadata`, `get_cover`, `download_cover`, `bulk_search`).
   - Collects exhaustive, raw metadata about the book, and downloads the best available cover image.
   - **Output:** Saves the completely unedited, raw metadata and the path to the downloaded cover directly into the agent state.

3. **Cover Agent**: Acts as a strict cover art validator.
   - Visually inspects the downloaded cover image using an advanced vision model to ensure the text matches the expected title and author.
   - **Fallback:** If the cover is incorrect (or missing), it uses a DuckDuckGo image search to scrape the web for a better, alternative high-resolution cover.
   - **Output:** Validates the cover and finalizes the verified cover URL and path in the state.

4. **Books Pipeline (Sequential Loop)**:
   - **Researcher Agent**: Performs exhaustive web searching (via DuckDuckGo) and web scraping to gather supplemental historical context, biographical facts, and critical reception.
   - **Writer Agent**: Synthesizes the raw metadata and research into a purely factual, fluff-free Editor.js recommendation.
   - **Critic Agent**: A ruthless gatekeeper that validates the draft, ensuring absolutely zero filler words, encyclopedic generalities, or em-dashes (—). If it fails, it is sent back to the Writer.
   - **Publisher Agent**: Takes the fully approved draft and publishes it live to the Igbo Archives database via MCP.

## How to Run

- **Local Polling/Testing**: `python app.py` (ensure `.env` has `TELEGRAM_BOT_TOKEN` and `GEMINI_API_KEY`). You can trigger the pipeline by sending "start" in Telegram.
- **Production Webhook**: Uses FastAPI + uvicorn via `render.yaml` and is configured to receive events at the `/webhook` endpoint.
- **Testing Script**: `python test_pipeline.py` executes a simulated run in the CLI to test agent handoffs and tool routing.
