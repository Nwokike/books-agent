import asyncio
import json
from ddgs import DDGS
from google.adk.agents import Agent, Context
from ..utils.resilience import ResilientGemini
from ..mcp_client import call_mcp_tool

__all__ = ["metadata_agent"]

async def duckduckgo_web_search(query: str) -> str:
    """Fallback search if book metadata tools fail to find the book."""
    try:
        def _search():
            results = DDGS().text(query, max_results=5)
            results = list(results)
            if not results:
                return "No results found."
            return "\n\n".join([f"Source: {r.get('title', '')}\nLink: {r.get('href', '')}\nSnippet: {r.get('body', '')}" for r in results])
            
        return await asyncio.to_thread(_search)
    except Exception as e:
        return f"Search failed: {str(e)}"

# --- The 6 book-metadata MCP Tools ---

async def mcp_search_book(title: str, author: str = "", isbn: str = "") -> str:
    """Search for a book across Google Books and Open Library."""
    kwargs = {"title": title}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    res = await call_mcp_tool("book-metadata", "search_book", kwargs)
    return json.dumps(res)

async def mcp_find_book(title: str, author: str = "", isbn: str = "") -> str:
    """Find a book and return complete information in one call. Recommended for full lookup."""
    kwargs = {"title": title}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    res = await call_mcp_tool("book-metadata", "find_book", kwargs)
    return json.dumps(res)

async def mcp_get_metadata(title: str, author: str = "", isbn: str = "") -> str:
    """Get comprehensive book metadata without cover lookup."""
    kwargs = {"title": title}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    res = await call_mcp_tool("book-metadata", "get_metadata", kwargs)
    return json.dumps(res)

async def mcp_get_cover(title: str, author: str = "", isbn: str = "", verify_dimensions: bool = False) -> str:
    """Get the best available cover image URL for a book."""
    kwargs = {"title": title, "verify_dimensions": verify_dimensions}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    res = await call_mcp_tool("book-metadata", "get_cover", kwargs)
    return json.dumps(res)

async def mcp_download_cover(title: str, author: str = "", isbn: str = "", save_path: str = "") -> str:
    """Download the best available cover image and save to disk."""
    kwargs = {"title": title}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    if save_path: kwargs["save_path"] = save_path
    res = await call_mcp_tool("book-metadata", "download_cover", kwargs)
    return json.dumps(res)

async def mcp_bulk_search(books_json_array: str) -> str:
    """Search for multiple books at once. Input must be a JSON array string."""
    res = await call_mcp_tool("book-metadata", "bulk_search", {"books": books_json_array})
    return json.dumps(res)

# --- State Injection Tool ---

async def save_raw_metadata_to_state(ctx: Context, metadata_json: str) -> str:
    """Saves the completely unedited, raw metadata to the agent's state. 
    This MUST be the final step after successfully finding the book data."""
    try:
        data = json.loads(metadata_json)
        ctx.state["raw_metadata"] = data
        return "SUCCESS: Raw metadata saved to state."
    except Exception as e:
        return f"ERROR saving to state: {str(e)}"

metadata_agent = Agent(
    name="MetadataAgent",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=["models/gemini-3-flash-preview"]
    ),
    description="Agent: Gathers exhaustive, unedited raw metadata for a discovered book using MCP tools.",
    tools=[
        mcp_search_book, 
        mcp_find_book, 
        mcp_get_metadata, 
        mcp_get_cover, 
        mcp_download_cover, 
        mcp_bulk_search,
        duckduckgo_web_search,
        save_raw_metadata_to_state
    ],
    instruction="""
ROLE: Master Archivist and Data Gatherer.

GOAL: You are given a target title and author. You must use your tools to fetch every single piece of information available about this book and save it to the state.

STRICT WORKFLOW:
1. Identify the input title and author from the user prompt.
2. Call `mcp_find_book` FIRST. It is the most comprehensive tool.
3. If `mcp_find_book` fails or lacks data, try `mcp_search_book` or `mcp_get_metadata`.
4. If the MCP tools return an error or cannot find the book, USE `duckduckgo_web_search` to find basic information about the book.
5. You MUST save the final, best data payload to state. Use `save_raw_metadata_to_state` and pass the raw JSON string you received. DO NOT EDIT OR SUMMARIZE THE DATA. Pass the exact raw JSON object you got from the MCP tool (or construct a raw JSON object from DDGS facts if MCP completely failed).
6. Once you receive "SUCCESS: Raw metadata saved to state.", you are done. Simply reply "Metadata gathering complete."

CRITICAL: You MUST use `save_raw_metadata_to_state` to succeed.
""".strip()
)
