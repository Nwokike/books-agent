import json
import uuid
from google.genai import types
from google.adk.agents import Agent, LoopAgent, BaseAgent, Context
from ..utils.resilience import ResilientGemini
from google.adk.events import Event, EventActions
from typing import List, Optional
from ..schema import BookRecommendationCreate, EditorJsContent, EditorJsBlock, EditorJsBlockData

__all__ = ["writer_loop"]

async def draft_book(ctx: Context, book_title: str, author: str, content_texts: List[str], isbn: Optional[str] = None, publication_year: Optional[int] = None, publisher: Optional[str] = None) -> str:
    """Takes a list of finalized content paragraphs, packages them into Editor.js json format, and saves the draft."""
    try:
        blocks = []
        for text in content_texts:
            blocks.append(
                EditorJsBlock(
                    id=f"block_{uuid.uuid4().hex[:8]}",
                    type="paragraph",
                    data=EditorJsBlockData(text=text)
                )
            )
            
        ext_url = ctx.state.get("external_url")
        if ext_url == "NONE":
            ext_url = None
            
        draft = BookRecommendationCreate(
            book_title=book_title,
            author=author,
            title=book_title, # defaults to book_title per schema
            isbn=isbn,
            publication_year=publication_year,
            publisher=publisher,
            external_url=ext_url, 
            cover_image=ctx.state.get("verified_cover_url"), 
            content_json=EditorJsContent(blocks=blocks)
        )
        
        draft_json = draft.model_dump()
        ctx.state["draft_notes"] = json.dumps({"status": "SUCCESS", "draft": draft_json})
        return json.dumps({"status": "SUCCESS", "message": "Draft saved successfully to state."})
    except Exception as e:
        return json.dumps({"status": "FAILURE", "error": str(e)})

writer = Agent(
    name="WriterAgent",
    model=ResilientGemini(
        model="models/gemma-4-31b-it",
        fallbacks=["models/gemma-4-26b-a4b-it"]
    ),
    description="Agent: Synthesizes research into a concise, purely factual book recommendation without fluff.",
    tools=[draft_book],
    output_key="draft_notes",
    instruction="""
ROLE: Lead Book Reviewer and Literary Synthesizer.

GOAL: Synthesize provided metadata and research into a high-quality, purely factual book recommendation.

AVAILABLE DATA:
- Target Book: {target_title} by {target_author}
- Raw Metadata: {raw_metadata}
- Cover Analysis: {media_report}
- Research Record: {research_context}

STRICT WRITING RULES:
1. ZERO FLUFF: Never write introductory sentences, conclusions, or generic cultural overviews. Go straight to the specific facts.
2. NO EM-DASHES: You are strictly forbidden from using em-dashes (—). Use commas, colons, or parentheses instead.
3. CONTENT STRUCTURE: Separate your thoughts into distinct paragraphs. You MUST include exactly one paragraph dedicated to the author's biography and their cultural/literary significance.
4. ORGANIC CITATIONS: If the Research agent provides a source URL, weave it naturally into the narrative using HTML anchor tags with the actual title. Do not cite every single sentence; prioritize citing unique or primary claims.
5. NO FORCED CITATIONS: If no specific URL is provided for a fact, do NOT try to force a citation.
6. FORMATTING: NEVER use literal newline characters (\n). Use HTML `<br><br>` for line breaks between paragraphs. NEVER use Markdown formatting like `**` or `*`. Use standard HTML tags like `<b>` or `<i>` for emphasis.
7. TOOL CALL: Call `draft_book` with the title, author, any available isbn/publication_year, and your formulated content texts (as a list of strings, one string per paragraph).
""".strip()
)

critic = Agent(
    name="CriticAgent",
    model=ResilientGemini(
        model="models/gemma-4-26b-a4b-it",
        fallbacks=["models/gemma-4-31b-it"]
    ),
    description="Agent: A ruthless gatekeeper that validates drafts against strict standards.",
    output_key="critic_status",
    instruction="""
ROLE: Elite Literary Validator.

GOAL: Review drafts for maximum factual density and absolute zero fluff.

AVAILABLE DRAFT: {draft_notes}

STRICT REJECTION CRITERIA:
1. REJECT if the draft contains ANY em-dashes (—). This is an absolute rule.
2. REJECT if the draft contains conversational filler (e.g., "It is important to note," "In summary"). Factual transitions (e.g., "Regarding the author," "In a historical context") are PERMITTED.
3. REJECT if the author's biography is missing or does not have its own dedicated paragraph.
4. REJECT if citations feel robotic, repetitive, or are awkwardly forced (e.g., identical structure used for 3+ consecutive sentences).
5. REJECT if invalid formatting is used: literal `\\n` characters instead of `<br><br>`, `**bold**` or `*italics*` instead of HTML tags.

OUTPUT: Reply with APPROVED if the text is flawless. Otherwise, list the specific rejection reasons.
""".strip()
)

class CriticEscalationChecker(BaseAgent):
    """A deterministic agent that checks the critic's status and terminates the loop."""
    name: str = "escalation_checker"
    
    async def _run_async_impl(self, context):
        status = context.session.state.get("critic_status", "")
        
        if "APPROVED" in status.upper():
            yield Event(
                author=self.name, 
                actions=EventActions(escalate=True)
            )
        else:
            yield Event(
                author=self.name,
                content=types.Content(
                    role="system",
                    parts=[types.Part.from_text(text="Draft not approved. Continuing refinement loop.")]
                )
            )

escalation_checker = CriticEscalationChecker()

writer_loop = LoopAgent(
    name="WriterLoop",
    max_iterations=5,
    sub_agents=[writer, critic, escalation_checker],
    description="Loop Agent: Generates and evaluates the book recommendation."
)
