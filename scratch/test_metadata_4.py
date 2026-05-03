import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from metadata.agent import mcp_bulk_search

async def test():
    print("Testing Metadata tool: mcp_bulk_search")
    books = [
        {"title": "Dune", "author": "Frank Herbert"},
        {"title": "1984", "author": "George Orwell"}
    ]
    try:
        res = await mcp_bulk_search(json.dumps(books))
        print("RESULT:")
        print(res)
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
