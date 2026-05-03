import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from metadata.agent import mcp_download_cover

async def test():
    print("Testing Metadata tool: mcp_download_cover")
    save_path = os.path.join(os.getcwd(), "temp", "test_download.jpg")
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    try:
        res = await mcp_download_cover("Efuru", save_path=save_path)
        print("RESULT:")
        print(res)
        if os.path.exists(save_path):
            print(f"File downloaded successfully to {save_path}")
        else:
            print("File not found after download.")
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
