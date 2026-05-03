import asyncio
import json
import sys
import os
from dotenv import load_dotenv

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))
load_dotenv()

from cover.agent import verify_local_cover_image

class MockContext:
    def __init__(self, state=None):
        self.state = state or {}

async def test():
    print("Testing Cover tool: verify_local_cover_image")
    ctx = MockContext(state={
        "target_title": "Efuru",
        "target_author": "Flora Nwapa",
        "raw_metadata": {
            "cover_url": "https://covers.openlibrary.org/b/id/275035-L.jpg"
        }
    })
    try:
        res = await verify_local_cover_image(ctx)
        print("RESULT:")
        print(res)
        print("State media_path:", ctx.state.get("media_path"))
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
