"""PDF text extraction using Docling (IBM)."""

import re
from pathlib import Path
from typing import Optional

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from .models import ExtractedPage, ExtractedDocument


class PDFExtractor:
    """Extract text and metadata from PDF files using Docling."""

    def __init__(self, enable_ocr: bool = True):
        """
        Initialize the PDF extractor.

        Args:
            enable_ocr: Enable OCR for scanned documents (default: True)
        """
        self.enable_ocr = enable_ocr
        self._converter: Optional[DocumentConverter] = None

    def _get_converter(self) -> DocumentConverter:
        """Lazy initialization of the document converter."""
        if self._converter is None:
            pipeline_options = PdfPipelineOptions(do_ocr=self.enable_ocr)
            pipeline_options.images_scale = 2.0
            pipeline_options.generate_page_images = False
            pipeline_options.generate_picture_images = False

            self._converter = DocumentConverter(
                allowed_formats=[InputFormat.PDF],
                format_options={
                    InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
                }
            )
        return self._converter

    def extract(self, file_path: str | Path) -> ExtractedDocument:
        """
        Extract text and metadata from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            ExtractedDocument with all pages and metadata
        """
        file_path = Path(file_path)
        converter = self._get_converter()

        # Convert the document
        result = converter.convert(file_path)
        doc = result.document

        # Get full markdown
        full_markdown = doc.export_to_markdown()

        # Extract metadata from docling document
        metadata = {}
        if hasattr(doc, 'origin') and doc.origin:
            if hasattr(doc.origin, 'filename'):
                metadata['title'] = doc.origin.filename

        # Build page-by-page content
        pages = []
        page_texts = self._split_by_pages(full_markdown, doc)

        for page_num, page_text in enumerate(page_texts, start=1):
            # Clean text
            cleaned_text = self._clean_text(page_text)

            # Count words
            words = cleaned_text.split()
            word_count = len(words)

            # Detect tables (heuristic: markdown tables have |)
            has_tables = '|' in page_text and '---' in page_text

            # Detect images (markdown image syntax)
            has_images = bool(re.search(r'!\[.*?\]\(.*?\)', page_text))

            pages.append(ExtractedPage(
                page_number=page_num,
                text=cleaned_text,
                char_count=len(cleaned_text),
                word_count=word_count,
                has_images=has_images,
                has_tables=has_tables,
            ))

        # Build result
        extracted = ExtractedDocument(
            filename=file_path.name,
            total_pages=len(pages) if pages else 1,
            pages=pages,
            title=metadata.get('title'),
            author=None,
            subject=None,
            keywords=None,
            creator=None,
            producer=None,
        )

        extracted.compute_metrics()
        return extracted

    def extract_markdown(self, file_path: str | Path) -> str:
        """
        Extract the full document as markdown.

        This is the primary output format - structured markdown
        with headings, lists, tables preserved.

        Args:
            file_path: Path to the PDF file

        Returns:
            Full document as markdown string
        """
        file_path = Path(file_path)
        converter = self._get_converter()

        result = converter.convert(file_path)
        return result.document.export_to_markdown()

    def _split_by_pages(self, markdown: str, doc) -> list[str]:
        """
        Split markdown content by pages.

        Docling doesn't always preserve page boundaries clearly,
        so we use heuristics or fall back to treating as single page.
        """
        # Try to find page markers if present
        # Docling sometimes adds <!-- page X --> comments
        page_pattern = r'<!-- page (\d+) -->'
        page_splits = re.split(page_pattern, markdown)

        if len(page_splits) > 1:
            # We have page markers
            pages = []
            for i in range(1, len(page_splits), 2):
                if i + 1 < len(page_splits):
                    pages.append(page_splits[i + 1])
            return pages if pages else [markdown]

        # No page markers - try to estimate from document structure
        # For now, return as single "page" with all content
        # The actual page count will be determined by the PDF reader
        return [markdown]

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        # Remove excessive whitespace but preserve paragraph structure
        lines = text.split('\n')
        cleaned_lines = [line.rstrip() for line in lines]
        text = '\n'.join(cleaned_lines)

        # Remove more than 2 consecutive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()
