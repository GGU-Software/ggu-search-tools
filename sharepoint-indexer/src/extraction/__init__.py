"""PDF text extraction module.

Uses lazy imports to avoid loading heavy dependencies (Docling) unless needed.
"""

from .models import ExtractedPage, ExtractedDocument
from .validator import DocumentValidator, ValidationResult, QualityIssue

# Lazy import for PDFExtractor to avoid loading Docling/pandas/numpy
# when only the validator is needed
def __getattr__(name):
    if name == "PDFExtractor":
        from .pdf_extractor import PDFExtractor
        return PDFExtractor
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "PDFExtractor",
    "ExtractedPage",
    "ExtractedDocument",
    "DocumentValidator",
    "ValidationResult",
    "QualityIssue",
]
