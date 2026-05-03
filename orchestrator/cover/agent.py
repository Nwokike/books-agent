import os
import io
import base64
import asyncio
import httpx
import PIL.Image
from ddgs import DDGS
from google.adk.agents import Agent, Context
from google.genai import types
from google import genai
from ..utils.resilience import ResilientGemini

__all__ = ["cover_agent"]

def _encode_and_compress_image(image_path: str, max_size=(1024, 1024)) -> str:
    with PIL.Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail(max_size)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

async def verify_local_cover_image(ctx: Context) -> str:
    """Visually inspects the downloaded cover image in the state."""
    target_title = ctx.state.get("target_title", "")
    target_author = ctx.state.get("target_author", "")
    
    # Check if we have a downloaded cover path
    # We will assume the metadata agent saves the path to state or we pull it from raw_metadata
    raw_metadata = ctx.state.get("raw_metadata", {})
    cover_url = raw_metadata.get("cover_url", "")
    
    if not cover_url:
        return "ERROR: No cover URL available in metadata."

    temp_path = f"temp/cover_{target_title.replace(' ', '_')}.jpg"
    os.makedirs("temp", exist_ok=True)
    
    try:
        # Download image
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(cover_url)
            resp.raise_for_status()
            with open(temp_path, "wb") as f:
                f.write(resp.content)
                
        # Vision Verification
        base64_image = _encode_and_compress_image(temp_path)
        genai_client = genai.Client(http_options=types.HttpOptions(timeout=120_000))
        
        prompt = (
            "ROLE: Elite Book Cover Verifier.\n"
            "GOAL: Examine this book cover and verify it matches the metadata.\n"
            f"EXPECTED METADATA: Title: '{target_title}', Author: '{target_author}'\n"
            "STRICT RULES:\n"
            "1. Read the text on the cover.\n"
            "2. Does it clearly say the title or author? If so, state 'VERIFIED' and provide a brief description.\n"
            "3. If it is completely the wrong book, state 'REJECTED' and explain why.\n"
            "4. Be lenient: if the cover is abstract but seems plausible, accept it."
        )
        
        response = await genai_client.aio.models.generate_content(
            model="models/gemma-4-31b-it",
            contents=[prompt, types.Part.from_bytes(data=base64.b64decode(base64_image), mime_type="image/jpeg")]
        )
        
        result_text = response.text
        
        if "REJECTED" in result_text.upper():
            return f"COVER REJECTED. Explanation: {result_text}"
            
        ctx.state["media_path"] = temp_path
        ctx.state["media_report"] = result_text
        ctx.state["verified_cover_url"] = cover_url
        return f"COVER VERIFIED. Report: {result_text}"
    except Exception as e:
        return f"ERROR verifying cover: {str(e)}"

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
        async with httpx.AsyncClient(timeout=30.0) as client:
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
    description="Agent: Verifies the book cover and finds a replacement if necessary.",
    tools=[verify_local_cover_image, duckduckgo_image_search, download_alternative_cover],
    instruction="""
ROLE: Cover Art Specialist.

GOAL: Ensure the target book has a valid, accurate cover image.

WORKFLOW:
1. ALWAYS start by calling `verify_local_cover_image` to check the cover retrieved by the Metadata agent.
2. If the tool returns "COVER VERIFIED", your job is done. Reply "Cover successfully verified."
3. If the tool returns "COVER REJECTED" or "ERROR", you MUST find a better cover.
4. Use `duckduckgo_image_search` with a specific query (e.g., "[Title] by [Author] book cover high resolution").
5. Pick the best image URL from the results.
6. Use `download_alternative_cover` with that exact URL.
7. Once successfully downloaded, reply "Alternative cover successfully acquired."
""".strip()
)
