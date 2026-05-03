import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from metadata.agent import save_raw_metadata_to_state

class MockContext:
    def __init__(self, state=None):
        self.state = state or {}

async def test():
    print("Testing Metadata tool: save_raw_metadata_to_state")
    ctx = MockContext()
    data = {"title": "Efuru", "author": "Flora Nwapa"}
    try:
        res = await save_raw_metadata_to_state(ctx, json.dumps(data))
        print("RESULT:")
        print(res)
        print("State raw_metadata:", ctx.state.get("raw_metadata"))
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
