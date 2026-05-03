import asyncio
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from cover.agent import duckduckgo_image_search

async def test():
    print("Testing Cover tool: duckduckgo_image_search")
    try:
        res = await duckduckgo_image_search("Efuru book cover")
        print("RESULT:")
        print(res)
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
