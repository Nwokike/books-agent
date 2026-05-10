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
from ..utils.resilience import ResilientGemini
from ..mcp_client import call_mcp_tool
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
    """Downloads an alternative cover from a URL. Returns the file path."""
    target_title = ctx.state.get("target_title", "Unknown")
    temp_path = f"temp/alt_cover_{target_title.replace(' ', '_')}.jpg"
    os.makedirs("temp", exist_ok=True)
    
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            resp = await client.get(image_url)
            resp.raise_for_status()
            with open(temp_path, "wb") as f:
                f.write(resp.content)
        
        return json.dumps({"saved": temp_path, "source_url": image_url})
    except Exception as e:
        return json.dumps({"error": f"Failed to download alternative cover: {str(e)}"})

async def save_verified_cover_to_state(ctx: Context, verified_url: str, file_path: str, report: str) -> str:
    """Updates the state with the final, verified cover information. This must be your final step."""
    ctx.state["verified_cover_url"] = verified_url
    ctx.state["media_path"] = file_path
    ctx.state["media_report"] = report
    return "SUCCESS: Verified cover information saved to state."

cover_agent = Agent(
    name="CoverAgent",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=[
            "models/gemma-4-26b-a4b-it",
            "models/gemini-3.1-flash-lite-preview",
            "models/gemini-3-flash-preview"
        ]
    ),
    description="Agent: Manages book cover acquisition and verification.",
    tools=[
        mcp_get_cover, 
        mcp_download_cover, 
        execute_vision_analysis, 
        duckduckgo_image_search, 
        download_alternative_cover,
        save_verified_cover_to_state
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
   - For ANY downloaded image (from MCP or fallback), you MUST call `execute_vision_analysis` passing the path returned by the tool.
4. FALLBACK:
   - If `mcp_download_cover` fails OR `execute_vision_analysis` returns "REJECTED" for the primary cover, you MUST use `duckduckgo_image_search` to find a high-resolution cover.
   - Pick the best URL, use `download_alternative_cover`, and then call `execute_vision_analysis` AGAIN on the new path.
5. FINALIZATION:
   - Once a cover is successfully verified, you MUST call `save_verified_cover_to_state` with the source URL, the local file path, and the vision report.
   - If you have exhausted all tools and still cannot find a verified cover, output EXACTLY: "COULD NOT FIND A COVER, USE DISCOVERY AGENT TO FIND ANOTHER BOOK".
   - Once you receive "SUCCESS: Verified cover information saved to state.", simply reply "Cover successfully acquired and verified."
""".strip()
)

root_agent = cover_agent