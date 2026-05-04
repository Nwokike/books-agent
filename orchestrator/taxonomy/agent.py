import json
from typing import AsyncGenerator
from google.genai import types
from google.adk.agents import Agent
from google.adk.models import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from ..mcp_client import call_mcp_tool

class BypassLlm(BaseLlm):
    """A mock LLM that does nothing, used for purely programmatic agents."""
    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        yield LlmResponse(text="Bypass", model="bypass")

async def mcp_taxonomy_fetcher() -> dict:
    """Fetches the list of authors from the Igbo Archives MCP server."""
    try:
        # Based on ArchiveAgent's successful pattern
        authors = await call_mcp_tool("igbo-archives", "list_authors", {})
        
        if "error" in authors:
            raise ValueError(f"Authors API Error: {authors['error']}")
            
        # Return a flat list of author names to keep it clean
        author_names = [a.get("name") for a in authors.get("results", []) if a.get("name")]
        return {"authors": author_names}
    except Exception as e:
        # Fallback to empty list if fetch fails, to allow pipeline to continue
        return {"authors": [], "error": str(e)}

async def fetch_taxonomy_programmatically(**kwargs) -> types.Content:
    """Programmatically provides live taxonomy data to the next agent."""
    taxonomies = await mcp_taxonomy_fetcher()
    return types.Content(
        role="model",
        parts=[types.Part.from_text(
            text=f"LIVE TAXONOMY DATA (For Writer Consistency):\n{json.dumps(taxonomies, indent=2)}"
        )]
    )

taxonomy_mapper = Agent(
    name="TaxonomyMapper",
    model=BypassLlm(model="bypass"),
    description="Agent: Deterministic taxonomy fetcher that ensures author consistency.",
    before_agent_callback=fetch_taxonomy_programmatically,
    instruction="Programmatic agent. Bypasses LLM to fetch data directly from the platform."
)
