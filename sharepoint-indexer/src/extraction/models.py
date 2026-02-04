"""Data models for extracted PDF content."""

from pydantic import BaseModel
from typing import Optional


class ExtractedPage(BaseModel):
    """Content extracted from a single PDF page."""

    page_number: int  # 1-indexed
    text: str
    char_count: int
    word_count: int
    has_images: bool
    has_tables: bool  # Heuristic detection


class ExtractedDocument(BaseModel):
    """Complete extracted content from a PDF document."""

    filename: str
    total_pages: int
    pages: list[ExtractedPage]

    # Metadata
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    creator: Optional[str] = None
    producer: Optional[str] = None

    # Quality metrics
    total_chars: int = 0
    total_words: int = 0
    pages_with_text: int = 0
    pages_with_images: int = 0
    avg_chars_per_page: float = 0.0

    # Potential issues
    likely_scanned: bool = False  # True if most pages have no text but have images

    def compute_metrics(self) -> None:
        """Compute aggregate metrics from pages."""
        self.total_chars = sum(p.char_count for p in self.pages)
        self.total_words = sum(p.word_count for p in self.pages)
        self.pages_with_text = sum(1 for p in self.pages if p.char_count > 50)
        self.pages_with_images = sum(1 for p in self.pages if p.has_images)
        self.avg_chars_per_page = self.total_chars / len(self.pages) if self.pages else 0

        # Heuristic: likely scanned if <20% of pages have text but >50% have images
        if self.total_pages > 0:
            text_ratio = self.pages_with_text / self.total_pages
            image_ratio = self.pages_with_images / self.total_pages
            self.likely_scanned = text_ratio < 0.2 and image_ratio > 0.5
