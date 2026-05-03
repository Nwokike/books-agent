import os
import io
import json
import base64
import asyncio
import httpx
import PIL.Image
from ddgs import DDGS
from google.adk.agents import Agent, Context
from google.genai import types
from google import genai
from utils.resilience import ResilientGemini
from mcp_client import call_mcp_tool
from .vision import execute_vision_analysis

__all__ = ["cover_agent"]

async def mcp_get_cover(title: str, author: str = "", isbn: str = "", verify_dimensions: bool = False) -> str:
    """Get the best available cover image URL for a book via MCP."""
    kwargs = {"title": title, "verify_dimensions": verify_dimensions}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    res = await call_mcp_tool("book-metadata", "get_cover", kwargs)
    return json.dumps(res)

async def mcp_download_cover(title: str, author: str = "", isbn: str = "", save_path: str = "") -> str:
    """Download the best available cover image and save to disk via MCP."""
    kwargs = {"title": title}
    if author: kwargs["author"] = author
    if isbn: kwargs["isbn"] = isbn
    if save_path: kwargs["save_path"] = save_path
    res = await call_mcp_tool("book-metadata", "download_cover", kwargs)
    return json.dumps(res)

async def duckduckgo_image_search(query: str) -> str:
    """Searches duckduckgo for an image matching the query and returns image URLs."""
    try:
        def _search():
            results = DDGS().images(query, max_results=3)
            results = list(results)
            if not results:
                return "No images found."
            return "\n".join([f"Image Title: {r.get('title')}\nURL: {r.get('image')}" for r in results])
        return await asyncio.to_thread(_search)
    except Exception as e:
        return f"Image search failed: {str(e)}"

async def download_alternative_cover(ctx: Context, image_url: str) -> str:
    """Downloads an alternative cover from a URL and saves it to state, overriding the bad one."""
    target_title = ctx.state.get("target_title", "Unknown")
    temp_path = f"temp/alt_cover_{target_title.replace(' ', '_')}.jpg"
    os.makedirs("temp", exist_ok=True)
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            with open(temp_path, "wb") as f:
                f.write(resp.content)
        
        ctx.state["media_path"] = temp_path
        ctx.state["verified_cover_url"] = image_url
        ctx.state["media_report"] = "Cover manually acquired via DuckDuckGo fallback and assumed valid."
        return f"SUCCESS: Alternative cover downloaded from {image_url} and saved to state."
    except Exception as e:
        return f"Failed to download alternative cover: {str(e)}"

cover_agent = Agent(
    name="CoverAgent",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=["models/gemma-4-26b-a4b-it"]
    ),
    description="Agent: Manages book cover acquisition and verification.",
    tools=[
        mcp_get_cover, 
        mcp_download_cover, 
        execute_vision_analysis, 
        duckduckgo_image_search, 
        download_alternative_cover
    ],
    instruction="""
ROLE: Cover Art Specialist and Visual Auditor.

GOAL: Ensure the target book has a valid, accurate cover image file saved on disk and verified.

STRICT WORKFLOW:
1. DATA CHECK: Look at `raw_metadata` in the state. 
2. ACQUISITION: 
   - If a `cover_url` exists in `raw_metadata`, call `mcp_download_cover` using that URL or the book details.
   - If no URL exists, or if you need a better one, call `mcp_get_cover` first, then `mcp_download_cover`.
3. VERIFICATION:
   - Once downloaded, call `execute_vision_analysis` passing the path returned by the download tool.
4. FALLBACK:
   - If `mcp_download_cover` fails OR `execute_vision_analysis` returns "REJECTED", you MUST use `duckduckgo_image_search` to find a high-resolution cover.
   - Pick the best URL and use `download_alternative_cover`.
5. FINALIZATION:
   - Once a cover is verified or a fallback is successfully downloaded, update `ctx.state["verified_cover_url"]` with the source URL, if you tried everything and still couldn't find a cover say "COULD NOT FIND A COVER, USE DISCOVERY AGENT TO FIND ANOTHER BOOK".
   - Reply "Cover successfully acquired and verified if successful."
""".strip()
)

root_agent = cover_agent