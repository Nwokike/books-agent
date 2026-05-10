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

async def mcp_bulk_search(books_json_array: str) -> str:
    """Search for multiple books at once. Input must be a JSON array string."""
    res = await call_mcp_tool("book-metadata", "bulk_search", {"books": books_json_array})
    return json.dumps(res)

# --- State Injection Tool ---

async def save_raw_metadata_to_state(ctx: Context, metadata_json: str, external_url: str = "NONE") -> str:
    """Saves the completely unedited, raw metadata and source URL to the state.
    This MUST be the final step after successfully finding the book data."""
    try:
        data = json.loads(metadata_json)
        ctx.state["raw_metadata"] = data
        if external_url != "NONE":
            ctx.state["external_url"] = external_url
        return "SUCCESS: Raw metadata and source URL saved to state."
    except Exception as e:
        return f"ERROR saving to state: {str(e)}"

metadata_agent = Agent(
    name="MetadataAgent",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=[
            "models/gemma-4-26b-a4b-it",
            "models/gemini-3.1-flash-lite-preview",
            "models/gemini-3-flash-preview"
        ]
    ),
    description="Agent: Gathers exhaustive, unedited raw metadata for a discovered book using MCP tools.",
    tools=[
        mcp_search_book, 
        mcp_find_book, 
        mcp_get_metadata, 
        mcp_bulk_search,
        duckduckgo_web_search,
        save_raw_metadata_to_state
    ],
    instruction="""
ROLE: Master Archivist and Data Gatherer.

GOAL: You are given a target title and author. You must use your tools to fetch every single piece of information available about this book and save it to the state.

STRICT WORKFLOW:
1. Identify the input title and author from the user prompt.
2. Call `mcp_find_book` FIRST to confirm the book exists before doing your main job which is use `mcp_get_metadata` to get the metadata of the book.
3. If and only if the mcp tools fail, use `duckduckgo_web_search` to find all available information about the book provided to you.
4. If the book does not exist anywhere simply report exactly: "book not found after extensive research, try to get another book from the discovery agent".
5. You MUST save the final, best data payload to state. Use `save_raw_metadata_to_state`. 
   - Pass the exact raw JSON string you received. 
   - If the MCP tool returned an authoritative source URL (like `openlibrary_url` or a Google Books link), pass it as the `external_url` argument.
6. Once you receive "SUCCESS: Raw metadata and source URL saved to state.", you are done. Simply reply "Metadata gathering complete."
""".strip()
)

root_agent = metadata_agent
