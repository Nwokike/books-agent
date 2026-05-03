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

# --- Wrapping Sub-Agents as Tools ---
discovery_tool = AgentTool(discovery_agent, skip_summarization=True)
metadata_tool = AgentTool(metadata_agent, skip_summarization=True)
cover_tool = AgentTool(cover_agent, skip_summarization=True)

# --- Pipeline ---
books_pipeline = SequentialAgent(
    name="BooksPipeline",
    sub_agents=[researcher_agent, writer_loop, publisher_agent],
    description="Pipeline: Researches, writes, and publishes the book record."
)

books_pipeline_tool = AgentTool(books_pipeline, skip_summarization=True)

# --- Orchestrator ---

def orchestrator_init(**kwargs) -> None:
    ctx = kwargs.get("context")
    # Initialize the state schema if it doesn't exist yet
    if ctx and "target_title" not in ctx.state:
        state_dict = BookState().model_dump()
        for k, v in state_dict.items():
            ctx.state[k] = v

def set_target_book(ctx: Context, title: str, author: str) -> str:
    """Updates the state with the discovered target book."""
    ctx.state["target_title"] = title
    ctx.state["target_author"] = author
    return f"State updated to target: {title} by {author}"

root_agent = Agent(
    name="Orchestrator",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=["models/gemma-4-26b-a4b-it"]
    ),
    description="The top-level orchestrator that completely automates book ingestion.",
    tools=[discovery_tool, metadata_tool, set_target_book, cover_tool, books_pipeline_tool],
    before_agent_callback=orchestrator_init,
    instruction="""
ROLE: Master Coordinator for Igbo Archives Books Ingestion.

GOAL: Run the full autonomous loop to ingest new books into the database without ANY human intervention.

STRICT WORKFLOW:
1. DISCOVERY: Call `DiscoveryAgent` tool to find a book NOT in the database.
   - It will return a JSON string with the title and author.
2. UPDATE STATE: Call `set_target_book` with the discovered title and author so the pipeline knows the target.
3. METADATA GATHERING: Call `MetadataAgent` tool, providing it the target title and author you just found.
   - It will fetch exhaustive metadata and sync it to the state automatically.
4. COVER VERIFICATION: Call `CoverAgent` tool. This agent will verify the cover downloaded by the Metadata Agent, and find a replacement if it's incorrect.
5. PIPELINE EXECUTION: Call `BooksPipeline` tool to run the final research, writing, and publishing phases.
   - The pipeline will handle everything else automatically.
6. COMPLETION: Report "Pipeline completed successfully" to the user.

CRITICAL RULES:
- Never ask the user for a book title. Use the DiscoveryAgent.
- Do not skip steps. This is a rigid, clinical process.
""".strip()
)