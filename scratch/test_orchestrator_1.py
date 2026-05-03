import asyncio
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from agent import set_target_book

class MockContext:
    def __init__(self, state=None):
        self.state = state or {}

async def test():
    print("Testing Orchestrator tool: set_target_book")
    ctx = MockContext()
    try:
        res = await set_target_book(ctx, "Omenuko", "Pita Nwana")
        print("RESULT:")
        print(res)
        print("State target_title:", ctx.state.get("target_title"))
        print("State target_author:", ctx.state.get("target_author"))
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
