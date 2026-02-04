"""
Data models for SharePoint documents.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    XLSX = "xlsx"
    TXT = "txt"
    UNKNOWN = "unknown"

    @classmethod
    def from_filename(cls, filename: str) -> "DocumentType":
        """Determine document type from filename extension."""
        ext = filename.lower().split(".")[-1] if "." in filename else ""
        mapping = {
            "pdf": cls.PDF,
            "docx": cls.DOCX,
            "doc": cls.DOCX,
            "xlsx": cls.XLSX,
            "xls": cls.XLSX,
            "txt": cls.TXT,
        }
        return mapping.get(ext, cls.UNKNOWN)


class SharePointDocument(BaseModel):
    """Metadata for a document in SharePoint."""

    # Identifiers
    id: str = Field(description="Graph API item ID")
    filename: str = Field(description="Original filename")

    # URLs
    web_url: str = Field(description="Clickable SharePoint URL")
    download_url: Optional[str] = Field(
        default=None,
        description="Temporary download URL (from @microsoft.graph.downloadUrl)"
    )

    # File info
    size: int = Field(description="File size in bytes")
    etag: str = Field(description="ETag for change detection")
    mime_type: Optional[str] = Field(default=None, description="MIME type")
    document_type: DocumentType = Field(description="Detected document type")

    # Timestamps
    created_at: datetime = Field(description="Creation timestamp")
    modified_at: datetime = Field(description="Last modification timestamp")

    # Authors
    created_by: Optional[str] = Field(default=None, description="Creator name")
    modified_by: Optional[str] = Field(default=None, description="Last modifier name")

    # Location
    parent_path: str = Field(description="Parent folder path in SharePoint")

    @property
    def title(self) -> str:
        """Extract title from filename (without extension)."""
        if "." in self.filename:
            return self.filename.rsplit(".", 1)[0]
        return self.filename

    def __str__(self) -> str:
        return f"{self.filename} ({self.size // 1024} KB)"


class FolderInfo(BaseModel):
    """Information about a folder to process."""
    id: str
    name: str
    url: str  # Graph API URL to fetch children
    depth: int = 0
