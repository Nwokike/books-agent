import asyncio
from ddgs import DDGS
from google.adk.agents import Agent
from utils.resilience import ResilientGemini
import httpx
from bs4 import BeautifulSoup

__all__ = ["researcher_agent"]

async def fetch_website_content(url: str) -> str:
    """Scrapes all readable body text content from a given URL, ignoring scripts and styles."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0, headers=headers) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Remove noisy elements
            for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                element.extract()
                
            text = soup.get_text(separator=' ', strip=True)
            
            if not text:
                return "No readable text found on the page."
            return f"Source URL: {url}\nContent:\n{text[:6000]}"
    except Exception as e:
        return f"Failed to fetch content from {url}: {str(e)}"

async def duckduckgo_web_search(query: str) -> str:
    """Searches the internet for historical and cultural context."""
    try:
        def _search():
            results = DDGS().text(query, max_results=4)
            results = list(results)
            if not results:
                return "No results found."
            return "\n\n".join([f"Source: {r.get('title', '')}\nLink: {r.get('href', '')}\nSnippet: {r.get('body', '')}" for r in results])
            
        return await asyncio.to_thread(_search)
    except Exception as e:
        return f"Search failed: {str(e)}"

researcher_agent = Agent(
    name="ResearcherAgent",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=["models/gemma-4-26b-a4b-it"]
    ),
    description="Agent: Gathers maximum supplemental context about the book and its author.",
    tools=[fetch_website_content, duckduckgo_web_search],
    output_key="research_context", 
    instruction="""
ROLE: Elite Literary Researcher.

GOAL: Gather as much highly specific supplemental context as possible about the target book and author.
You are researching beyond the basic metadata (publication year, basic description) to find historical context, cultural impact, critical reception, or author biography.

AVAILABLE DATA:
- Target Book: {target_title} by {target_author}
- Raw Metadata: {raw_metadata}

STRICT WORKFLOW:
1. ORIGINAL URL SCRAPING: If the metadata contains a relevant external URL (e.g., an Open Library link), call `fetch_website_content`.
2. EXHAUSTIVE WEB SEARCH: You MUST call `duckduckgo_web_search` multiple times. Search for critical reception, historical context of when the book was written, and biographical facts about the author's life that relate to the book.
3. OUTPUT: Output ALL the exact text/snippets caught from both the URL and searches, untouched and un-rewritten, with their Source Link/URLs. 

STRICT RULES:
- NO REWRITING. Do not summarize. Provide verbatim text.
- NO GENERAL TRIVIA. Provide highly specific facts relating to the book or author.
- If no specific supplemental context found, output EXACTLY: "No specific supplemental context found."
""".strip()
)
