import os
import json
import base64
import io
import asyncio
import httpx
import PIL.Image
from google import genai
from google.genai import types
from google.adk.agents import Agent, SequentialAgent, Context
from google.adk.tools import AgentTool

from .utils.resilience import ResilientGemini
from .schema import BookState

from .discovery.agent import discovery_agent
from .metadata.agent import metadata_agent
from .researcher.agent import researcher_agent
from .writer.agent import writer_loop
from .publisher.agent import publisher_agent
from .cover.agent import cover_agent
from .taxonomy.agent import taxonomy_mapper

# --- Wrapping Sub-Agents as Tools ---
discovery_tool = AgentTool(discovery_agent)
metadata_tool = AgentTool(metadata_agent)
cover_tool = AgentTool(cover_agent)

# --- Pipeline ---
books_pipeline = SequentialAgent(
    name="BooksPipeline",
    sub_agents=[researcher_agent, taxonomy_mapper, writer_loop, publisher_agent],
    description="Pipeline: Researches, writes, and publishes the book record."
)

# --- Orchestrator ---

def orchestrator_init(**kwargs) -> None:
    ctx = kwargs.get("context")
    # Initialize the state schema if it doesn't exist yet
    if ctx and "target_title" not in ctx.state:
        state_dict = BookState().model_dump()
        for k, v in state_dict.items():
            ctx.state[k] = v

async def set_target_book(ctx: Context, title: str, author: str, external_url: str = "NONE") -> str:
    """Updates the state with the discovered target book and optional source URL."""
    ctx.state["target_title"] = title
    ctx.state["target_author"] = author
    ctx.state["external_url"] = external_url
    return f"State updated to target: {title} by {author} (Source: {external_url})"

root_agent = Agent(
    name="Orchestrator",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=["models/gemma-4-26b-a4b-it"]
    ),
    description="The top-level orchestrator that completely automates book ingestion.",
    tools=[discovery_tool, metadata_tool, set_target_book, cover_tool],
    sub_agents=[books_pipeline],
    before_agent_callback=orchestrator_init,
    instruction="""
ROLE: Master Coordinator for Igbo Archives Books Ingestion.

GOAL: Run the full autonomous loop to ingest new books into the database without ANY human intervention.

STRICT WORKFLOW:
1. DISCOVERY: Call `DiscoveryAgent` tool, tell it exactly to find a book related to Igbo NOT in the database.
   - It will return a JSON string with the title and author.
2. UPDATE STATE: Call `set_target_book` with the discovered title, author, and the `external_url` (if provided by Discovery) so the pipeline knows the target and where to research.
3. METADATA GATHERING: Call `MetadataAgent` tool, providing it the target title and author you just found.
   - It will fetch exhaustive metadata and sync it to the state automatically.
4. COVER ACQUISITION & VERIFICATION: Call `CoverAgent` tool. This agent will now handle downloading and verifying the cover from the gathered metadata or finding an alternative.
5. PIPELINE EXECUTION: Call `BooksPipeline` tool to run the final research, writing, and publishing phases.
   - The pipeline will handle everything else automatically.
6. COMPLETION: Report "Pipeline completed successfully" to the user.

CRITICAL RULES:
- Never ask the user for a book title. Use the DiscoveryAgent.
- Do not skip steps. This is a rigid, clinical process.
- DO NOT output conversational filler or status updates to the user between workflow steps. You must chain the tool calls. Only output text when the ENTIRE workflow is completed.
""".strip()
)