import os
import base64
import io
import logging
import asyncio
from google import genai
from google.genai import types
import PIL.Image
from google.adk.agents import Context

logger = logging.getLogger(__name__)

def _encode_and_compress_image(image_path: str, max_size=(1024, 1024)) -> str:
    """Resizes the image to fit model limits and converts to base64."""
    with PIL.Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        img.thumbnail(max_size)
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

async def execute_vision_analysis(ctx: Context, file_path: str) -> str:
    """Visually inspects a book cover image on disk using Gemini Vision."""
    target_title = ctx.state.get("target_title", "")
    target_author = ctx.state.get("target_author", "")
    
    if not os.path.exists(file_path):
        return f"ERROR: File not found at {file_path}"
    
    try:
        base64_image = _encode_and_compress_image(file_path)
        client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY"),
            http_options=types.HttpOptions(timeout=120_000)
        )
        
        # Build a context-aware prompt using the book metadata
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
        
        models_to_try = [
            "models/gemma-4-31b-it", 
            "models/gemma-4-26b-a4b-it",
            "models/gemini-3.1-flash-lite-preview",
            "models/gemini-3-flash-preview"
        ]
        
        for model_name in models_to_try:
            try:
                response = await client.aio.models.generate_content(
                    model=model_name,
                    contents=[
                        prompt,
                        types.Part.from_bytes(
                            data=base64.b64decode(base64_image),
                            mime_type="image/jpeg"
                        )
                    ]
                )
                
                result_text = response.text
                
                if "REJECTED" in result_text.upper():
                    return f"COVER REJECTED. Explanation: {result_text}"
                
                return result_text
            except Exception:
                continue
                
        return "ERROR: Vision analysis failed after all retries."
    except Exception as e:
        return f"ERROR: {str(e)}"
