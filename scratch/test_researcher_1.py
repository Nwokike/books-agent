import asyncio
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from researcher.agent import fetch_website_content

async def test():
    print("Testing Researcher tool: fetch_website_content")
    url = "https://en.wikipedia.org/wiki/Efuru"
    try:
        res = await fetch_website_content(url)
        print("RESULT:")
        print(res[:500] + "...")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
