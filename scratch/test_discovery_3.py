import asyncio
import json
import sys
import os

# Add orchestrator to path
sys.path.append(os.path.join(os.getcwd(), "orchestrator"))

from discovery.agent import check_database

async def test():
    print("Testing Discovery tool: check_database")
    try:
        # Testing with a book likely to be in the database or not
        res = await check_database("Efuru", "Flora Nwapa")
        print("RESULT:")
        print(res)
    except Exception as e:
        print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test())
