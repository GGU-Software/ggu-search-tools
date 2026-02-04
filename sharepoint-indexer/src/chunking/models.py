"""Data models for document chunks."""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ChunkMetadata(BaseModel):
    """Metadata for a document chunk."""

    # Source document info
    document_id: str = Field(..., description="Unique document identifier (e.g., SharePoint item ID)")
    filename: str = Field(..., description="Original filename")
    source_url: Optional[str] = Field(None, description="URL to source document")

    # Position in document
    section_title: Optional[str] = Field(None, description="Section heading this chunk belongs to")
    section_path: Optional[str] = Field(None, description="Full path of nested sections (e.g., '4 > 4.1 > 4.1.2')")
    chunk_index: int = Field(..., description="Index of this chunk within the document")
    total_chunks: int = Field(0, description="Total chunks in document (set after chunking)")

    # Content info
    has_table: bool = Field(False, description="Whether chunk contains table data")
    has_list: bool = Field(False, description="Whether chunk contains list items")

    # Timestamps
    document_modified: Optional[datetime] = Field(None, description="When source document was last modified")
    indexed_at: Optional[datetime] = Field(None, description="When this chunk was indexed")


class Chunk(BaseModel):
    """A single chunk of document content ready for embedding."""

    id: str = Field(..., description="Unique chunk identifier")
    content: str = Field(..., description="The text content of the chunk")
    metadata: ChunkMetadata = Field(..., description="Chunk metadata for filtering and context")

    # Metrics
    char_count: int = Field(0, description="Character count")
    word_count: int = Field(0, description="Approximate word count")

    def compute_metrics(self) -> None:
        """Compute char and word counts."""
        self.char_count = len(self.content)
        self.word_count = len(self.content.split())

    @property
    def is_empty(self) -> bool:
        """Check if chunk has meaningful content."""
        return self.word_count < 10
