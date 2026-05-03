import asyncio
import json
import sys
import os
from dotenv import load_dotenv

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))
load_dotenv()

from publisher.agent import execute_mcp_publish

class MockContext:
    def __init__(self, state=None):
        self.state = state or {}

async def test():
    print("Testing Publisher tool: publish_book_recommendation")
    # Prepare a mock draft
    draft_data = {
        "book_title": "Efuru",
        "author": "Flora Nwapa",
        "title": "Efuru",
        "isbn": "9781035900534",
        "publication_year": 1966,
        "publisher": "Heinemann",
        "cover_image": "https://covers.openlibrary.org/b/id/275035-L.jpg",
        "content_json": {"blocks": [{"type": "paragraph", "data": {"text": "A pioneer work of African literature."}}]}
    }
    ctx = MockContext(state={
        "draft_notes": json.dumps({"status": "SUCCESS", "draft": draft_data})
    })
    try:
        res = await execute_mcp_publish(draft_data)
        print("RESULT:")
        print(res)
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
