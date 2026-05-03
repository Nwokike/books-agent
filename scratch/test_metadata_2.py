import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from metadata.agent import mcp_get_cover

async def test():
    print("Testing Metadata tool: mcp_get_cover")
    try:
        res = await mcp_get_cover("Efuru")
        print("RESULT:")
        print(res)
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
