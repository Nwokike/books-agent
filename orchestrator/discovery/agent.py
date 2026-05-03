import asyncio
import json
from ddgs import DDGS
from google.adk.agents import Agent
from ..utils.resilience import ResilientGemini
from ..mcp_client import call_mcp_tool

__all__ = ["discovery_agent"]

async def mcp_search_book(title: str, author: str = "", isbn: str = "") -> str:
    """Search for a book across Google Books and Open Library."""
    kwargs = {"title": title}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    res = await call_mcp_tool("book-metadata", "search_book", kwargs)
    return json.dumps(res)

async def mcp_find_book(title: str, author: str = "", isbn: str = "") -> str:
    """Find a book and return complete information in one call."""
    kwargs = {"title": title}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    res = await call_mcp_tool("book-metadata", "find_book", kwargs)
    return json.dumps(res)

async def duckduckgo_web_search(query: str) -> str:
    """Searches the internet for lists of books or authors to discover."""
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

async def check_database(title: str, author: str) -> str:
    """Checks if a book already exists in the database. Returns 'EXISTS' or 'NOT_FOUND'."""
    try:
        response = await call_mcp_tool("igbo-archives", "list_books")
        if "error" in response:
            return f"Error checking database: {response['error']}"
            
        books = response.get("items", [])
        
        # Simple normalization check
        t_norm = title.lower().strip()
        a_norm = author.lower().strip()
        
        for book in books:
            db_title = book.get("title", "").lower().strip()
            db_author = book.get("author", "").lower().strip()
            
            if t_norm in db_title or db_title in t_norm:
                return "EXISTS: A book with a very similar title is already in the database."
            
            if book.get("book_title", ""):
                db_b_title = book.get("book_title", "").lower().strip()
                if t_norm in db_b_title or db_b_title in t_norm:
                    return "EXISTS: A book with a very similar title is already in the database."

        return "NOT_FOUND: Book does not exist in the database. Safe to proceed."
    except Exception as e:
        return f"Database check failed: {str(e)}"

discovery_agent = Agent(
    name="DiscoveryAgent",
    model=ResilientGemini(
        model="models/gemini-3.1-flash-lite-preview",
        fallbacks=["models/gemini-3-flash-preview"]
    ),
    description="Agent: Discovers culturally significant Igbo/African literature not yet in the database.",
    tools=[mcp_find_book, mcp_search_book, duckduckgo_web_search, check_database],
    instruction="""
ROLE: Elite Literary Scout for Igbo Archives.

GOAL: Find a culturally significant book related to Igbo people, culture, history, or written by an Igbo/African author that is NOT currently in the database.

WORKFLOW INSTRUCTIONS:
1. You have multiple tools to discover books. Your primary tools to find books are `mcp_find_book` and `mcp_search_book`. You can use them to explore literature.
2. If you are not getting what you want from the MCP tools (e.g., getting only generic results or no Igbo-specific results), you have the choice to use `duckduckgo_web_search` to search for Igbo-related books (e.g., "important Igbo books", "books by Nigerian authors").
3. Once you pick ONE specific book, USE `check_database` to see if we already have it. Provide the title and author.
4. If it returns "EXISTS", pick a different book.
5. If it returns "NOT_FOUND", stop immediately.

OUTPUT:
When you have found a book that is "NOT_FOUND" in the database, output EXACTLY the title and author in JSON format:
{
  "title": "Exact Title Here",
  "author": "Exact Author Here"
}

Do not output anything else. No conversational filler. Just the JSON.
""".strip()
)
