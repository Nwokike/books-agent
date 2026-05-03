import asyncio
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from metadata.agent import duckduckgo_web_search

async def test():
    print("Testing Metadata tool: duckduckgo_web_search")
    try:
        res = await duckduckgo_web_search("Flora Nwapa Efuru summary")
        print("RESULT:")
        print(res[:500] + "...")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
