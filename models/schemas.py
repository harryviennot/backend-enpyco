"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# === Memoire Schemas ===

class MemoireUploadResponse(BaseModel):
    """Response after uploading a memoire file."""
    id: str
    filename: str
    storage_path: str
    client: Optional[str] = None
    year: Optional[int] = None
    indexed: bool = False
    parsed: bool = False
    created_at: datetime


class MemoireMetadata(BaseModel):
    """Complete memoire metadata."""
    id: str
    filename: str
    storage_path: str
    client: Optional[str] = None
    year: Optional[int] = None
    indexed: bool = False
    created_at: datetime


class MemoireListResponse(BaseModel):
    """List of memoires."""
    memoires: List[MemoireMetadata]
    count: int


# === Parser Schemas ===

class ParsedSection(BaseModel):
    """A section extracted from a document."""
    title: Optional[str] = None
    content: str
    page: Optional[int] = None
    order: int


class ParseResult(BaseModel):
    """Result of parsing a document."""
    sections: List[ParsedSection]
    full_text: str
    page_count: Optional[int] = None
    paragraph_count: Optional[int] = None
    char_count: int
    metadata: Dict[str, Any] = {}


class ChunkData(BaseModel):
    """A text chunk for RAG."""
    content: str
    chunk_index: int
    char_start: int
    char_end: int
    metadata: Dict[str, Any] = {}


class ParseResponse(BaseModel):
    """Response after parsing a memoire."""
    memoire_id: str
    status: str
    chunks_created: int
    char_count: int
    parse_result: ParseResult


# === Project Schemas ===

class ProjectCreate(BaseModel):
    """Request to create a new project."""
    name: str = Field(..., min_length=1, max_length=255)


class ProjectResponse(BaseModel):
    """Response after creating a project."""
    id: str
    name: str
    status: str
    created_at: datetime


class ProjectMetadata(BaseModel):
    """Complete project metadata."""
    id: str
    name: str
    rc_storage_path: Optional[str] = None
    rc_context: Optional[str] = None
    status: str
    created_at: datetime


class RCUploadResponse(BaseModel):
    """Response after uploading RC."""
    project_id: str
    rc_uploaded: bool
    rc_storage_path: str


# === Section Schemas ===

class SectionData(BaseModel):
    """A generated section."""
    id: str
    project_id: str
    section_type: str
    title: str
    content: str
    order_num: int
    created_at: datetime


# === Health Check ===

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database: str = "connected"
    storage: str = "connected"
