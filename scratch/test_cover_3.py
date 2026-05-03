import asyncio
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from cover.agent import download_alternative_cover

class MockContext:
    def __init__(self, state=None):
        self.state = state or {}

async def test():
    print("Testing Cover tool: download_alternative_cover")
    ctx = MockContext(state={"target_title": "Efuru"})
    url = "https://m.media-amazon.com/images/I/51okRItmRjL._SL1000_.jpg"
    try:
        res = await download_alternative_cover(ctx, url)
        print("RESULT:")
        print(res)
        print("State media_path:", ctx.state.get("media_path"))
        print("State verified_cover_url:", ctx.state.get("verified_cover_url"))
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
