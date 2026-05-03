import json
from google.adk.agents import Agent
from ..utils.resilience import ResilientGemini
from ..mcp_client import call_mcp_tool

__all__ = ["publisher_agent"]

async def execute_mcp_publish(draft_dict: dict) -> str:
    """Accepts a draft object and publishes it to Igbo Archives via MCP."""
    try:
        response = await call_mcp_tool("igbo-archives", "create_books", {"body": draft_dict})
        if "error" in response:
            return f"Failed to publish: {response['error']}"
        else:
            return f"Published successfully! ID: {response.get('id', 'Unknown')}"
    except Exception as e:
        return str(e)


publisher_agent = Agent(
    name="PublisherAgent",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=["models/gemma-4-26b-a4b-it"]
    ),
    description="Agent: The final record publisher that submits the book recommendation.",
    tools=[execute_mcp_publish],
    instruction="""
ROLE:
You are the Final Executioner for the Igbo Archives.

GOAL:
Take the drafted book payload created by the Writer and push it to the live database, BUT ONLY if it passed validation.

AVAILABLE DATA:
- Critic Status: {critic_status}
- Draft Payload: {draft_notes}

STRICT RULES:
1. SAFETY CHECK: Check the Critic Status. If the status does not explicitly say "APPROVED", it means the draft failed validation after maximum retries. DO NOT call the tool. Instead, output: "❌ Pipeline aborted: The drafted book failed to pass the Critic's validation standards."
2. PUBLISH: If the Critic Status is "APPROVED", parse the success JSON object in the Draft Payload. Extract the `draft` dictionary.
3. Pass the extracted `draft` dictionary directly to `execute_mcp_publish`. Do not stringify it.
4. Output the success or failure results to the user.
""".strip()
)
