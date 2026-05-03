import asyncio
import sys
import os
from dotenv import load_dotenv

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))
load_dotenv()

from writer.agent import draft_book

class MockContext:
    def __init__(self, state=None):
        self.state = state or {}

async def test():
    print("Testing Writer tool: draft_book")
    ctx = MockContext(state={
        "target_title": "Efuru",
        "target_author": "Flora Nwapa",
        "raw_metadata": {"description": "A book about an Igbo woman."},
        "verified_cover_url": "https://covers.openlibrary.org/b/id/275035-L.jpg",
        "research_context": "Flora Nwapa was a pioneer..."
    })
    try:
        res = await draft_book(ctx, "Efuru", "Flora Nwapa", ["Flora Nwapa", "Igbo woman", "Uhamiri"])
        print("RESULT:")
        print(res[:500] + "...")
        print("State draft_notes:", ctx.state.get("draft_notes")[:100] + "...")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
