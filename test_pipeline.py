import asyncio
import os
import uuid
from dotenv import load_dotenv

# Load .env
load_dotenv()

from orchestrator.agent import root_agent
from google.adk.runners import Runner
from google.genai import types
from google.adk.sessions.in_memory_session_service import InMemorySessionService

async def main():
    print("Testing BooksAgent pipeline. Checking for API keys...")
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not found.")
        return
        
    print("Initializing Runner...")
    runner = Runner(
        app_name="books-agent-tester",
        agent=root_agent,
        session_service=InMemorySessionService(),
    )

    session = await runner.session_service.create_session(app_name="books-agent-tester", user_id="test_user")
    
    print("Sending 'start' message to orchestrator...")
    print("-" * 50)
    
    try:
        msg = types.Content(role="user", parts=[types.Part.from_text(text="start")])
        async for event in runner.run_async(user_id="test_user", session_id=session.id, new_message=msg):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"[{event.author}] {part.text}")
                    elif part.thought:
                        print(f"[{event.author} THOUGHT] {part.thought}")
            if hasattr(event, "actions") and event.actions and getattr(event.actions, "tool_calls", None):
                for call in event.actions.tool_calls:
                    print(f"[{event.author} SYSTEM] Calling tool {call.name}(...)")
    except Exception as e:
        print(f"\nPipeline failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(main())
