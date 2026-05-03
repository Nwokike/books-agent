from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

# EditorJS Schema
class EditorJsBlockData(BaseModel):
    text: str
    level: Optional[int] = None

class EditorJsBlock(BaseModel):
    id: str
    type: str
    data: EditorJsBlockData

class EditorJsContent(BaseModel):
    time: int = 1700000000000
    blocks: List[EditorJsBlock]
    version: str = "2.30.2"

class BookRecommendationCreate(BaseModel):
    book_title: str
    author: str
    title: str = Field(description="Must default to the book title")
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    external_url: Optional[str] = None
    cover_image: Optional[str] = None
    content_json: EditorJsContent

class BookState(BaseModel):
    target_title: str = "NONE"
    target_author: str = "NONE"
    
    # Metadata fields
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)
    external_url: str = "NONE"
    
    # Cover validation
    media_path: str = "NONE"
    media_report: str = "NONE"
    verified_cover_url: str = "NONE"
    
    # Text Generation
    research_context: str = "NONE"
    draft_notes: str = "NONE"
    critic_status: str = "PENDING"
