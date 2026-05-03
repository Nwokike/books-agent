import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from discovery.agent import mcp_search_book

async def test():
    print("Testing Discovery tool: mcp_search_book")
    try:
        res = await mcp_search_book("Efuru")
        print("RESULT:")
        print(res)
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
