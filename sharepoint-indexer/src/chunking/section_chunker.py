"""Section-aware document chunker for Markdown content."""

import re
import hashlib
from typing import Optional
from datetime import datetime

from .models import Chunk, ChunkMetadata


class SectionChunker:
    """
    Split Markdown documents into chunks respecting section boundaries.

    Strategy:
    1. Parse document into sections based on headings
    2. Split large sections into smaller chunks
    3. Preserve section context in metadata
    4. Add overlap between chunks for continuity
    """

    def __init__(
        self,
        max_chunk_size: int = 1500,
        min_chunk_size: int = 200,
        overlap_size: int = 100,
    ):
        """
        Initialize the chunker.

        Args:
            max_chunk_size: Maximum characters per chunk (default: 1500 ~ 300-400 tokens)
            min_chunk_size: Minimum characters for a standalone chunk (default: 200)
            overlap_size: Characters to overlap between chunks (default: 100)
        """
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size
        self.overlap_size = overlap_size

        # Regex to match markdown headings (## Heading)
        self.heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    def chunk_document(
        self,
        markdown: str,
        document_id: str,
        filename: str,
        source_url: Optional[str] = None,
        document_modified: Optional[datetime] = None,
    ) -> list[Chunk]:
        """
        Split a Markdown document into chunks.

        Args:
            markdown: The full document as Markdown
            document_id: Unique identifier for the source document
            filename: Original filename
            source_url: Optional URL to source document
            document_modified: Optional modification timestamp

        Returns:
            List of Chunk objects
        """
        # Parse into sections
        sections = self._parse_sections(markdown)

        # Create chunks from sections
        chunks = []
        chunk_index = 0

        for section in sections:
            section_chunks = self._chunk_section(
                section["content"],
                section["title"],
                section["path"],
                document_id=document_id,
                filename=filename,
                source_url=source_url,
                document_modified=document_modified,
                start_index=chunk_index,
            )
            chunks.extend(section_chunks)
            chunk_index += len(section_chunks)

        # Update total_chunks in metadata
        for chunk in chunks:
            chunk.metadata.total_chunks = len(chunks)

        return chunks

    def _parse_sections(self, markdown: str) -> list[dict]:
        """
        Parse Markdown into sections based on headings.

        Returns list of dicts with:
        - title: The heading text
        - level: Heading level (1-6)
        - path: Full section path (e.g., "4 > 4.1")
        - content: The content under this heading
        """
        sections = []
        heading_stack = []  # Track nested section titles

        # Find all headings with their positions
        headings = []
        for match in self.heading_pattern.finditer(markdown):
            level = len(match.group(1))
            title = match.group(2).strip()
            start = match.start()
            end = match.end()
            headings.append({
                "level": level,
                "title": title,
                "start": start,
                "end": end,
            })

        # If no headings, treat entire document as one section
        if not headings:
            return [{
                "title": None,
                "level": 0,
                "path": None,
                "content": markdown.strip(),
            }]

        # Content before first heading
        if headings[0]["start"] > 0:
            preamble = markdown[:headings[0]["start"]].strip()
            if preamble:
                sections.append({
                    "title": None,
                    "level": 0,
                    "path": None,
                    "content": preamble,
                })

        # Process each heading and its content
        for i, heading in enumerate(headings):
            # Update heading stack for path tracking
            while heading_stack and heading_stack[-1]["level"] >= heading["level"]:
                heading_stack.pop()
            heading_stack.append(heading)

            # Build section path
            path = " > ".join(h["title"] for h in heading_stack)

            # Get content until next heading (or end of document)
            content_start = heading["end"]
            if i + 1 < len(headings):
                content_end = headings[i + 1]["start"]
            else:
                content_end = len(markdown)

            content = markdown[content_start:content_end].strip()

            # Include the heading in content for context
            full_content = f"## {heading['title']}\n\n{content}" if content else f"## {heading['title']}"

            sections.append({
                "title": heading["title"],
                "level": heading["level"],
                "path": path,
                "content": full_content,
            })

        return sections

    def _chunk_section(
        self,
        content: str,
        section_title: Optional[str],
        section_path: Optional[str],
        document_id: str,
        filename: str,
        source_url: Optional[str],
        document_modified: Optional[datetime],
        start_index: int,
    ) -> list[Chunk]:
        """Split a section into appropriately sized chunks."""
        chunks = []

        # If section is small enough, return as single chunk
        if len(content) <= self.max_chunk_size:
            if len(content) >= self.min_chunk_size or not chunks:
                chunk = self._create_chunk(
                    content=content,
                    document_id=document_id,
                    filename=filename,
                    source_url=source_url,
                    section_title=section_title,
                    section_path=section_path,
                    chunk_index=start_index,
                    document_modified=document_modified,
                )
                chunks.append(chunk)
            return chunks

        # Split large sections by paragraphs first
        paragraphs = self._split_into_paragraphs(content)

        current_chunk = ""
        chunk_index = start_index

        for para in paragraphs:
            # If adding paragraph exceeds max size
            if len(current_chunk) + len(para) + 2 > self.max_chunk_size:
                if current_chunk:
                    # Save current chunk
                    chunk = self._create_chunk(
                        content=current_chunk.strip(),
                        document_id=document_id,
                        filename=filename,
                        source_url=source_url,
                        section_title=section_title,
                        section_path=section_path,
                        chunk_index=chunk_index,
                        document_modified=document_modified,
                    )
                    chunks.append(chunk)
                    chunk_index += 1
                    current_chunk = ""

                # Check if paragraph itself is too large and needs splitting
                if len(para) > self.max_chunk_size:
                    # Paragraph itself is too large, split it
                    # Check if it's a table (special handling)
                    if self._is_table(para):
                        para_chunks = self._split_large_table(
                            para,
                            document_id=document_id,
                            filename=filename,
                            source_url=source_url,
                            section_title=section_title,
                            section_path=section_path,
                            start_index=chunk_index,
                            document_modified=document_modified,
                        )
                    else:
                        para_chunks = self._split_large_text(
                            para,
                            document_id=document_id,
                            filename=filename,
                            source_url=source_url,
                            section_title=section_title,
                            section_path=section_path,
                            start_index=chunk_index,
                            document_modified=document_modified,
                        )
                    chunks.extend(para_chunks)
                    chunk_index += len(para_chunks)
                else:
                    # Paragraph fits in a new chunk, start accumulating
                    current_chunk = para
            else:
                # Add paragraph to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para

        # Don't forget the last chunk
        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                document_id=document_id,
                filename=filename,
                source_url=source_url,
                section_title=section_title,
                section_path=section_path,
                chunk_index=chunk_index,
                document_modified=document_modified,
            )
            chunks.append(chunk)

        return chunks

    def _split_into_paragraphs(self, text: str) -> list[str]:
        """Split text into paragraphs (double newline separated)."""
        # Split on double newlines, but keep tables together
        parts = re.split(r'\n\n+', text)
        return [p.strip() for p in parts if p.strip()]

    def _is_table(self, text: str) -> bool:
        """Check if text is a markdown table."""
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False
        # Tables have | in first line and |---| pattern in second line
        return '|' in lines[0] and bool(re.search(r'\|[-:]+\|', text))

    def _split_large_table(
        self,
        table_text: str,
        document_id: str,
        filename: str,
        source_url: Optional[str],
        section_title: Optional[str],
        section_path: Optional[str],
        start_index: int,
        document_modified: Optional[datetime],
    ) -> list[Chunk]:
        """Split a large markdown table into multiple chunks, preserving header."""
        chunks = []
        chunk_index = start_index

        lines = table_text.strip().split('\n')
        if len(lines) < 3:
            # Not a proper table, treat as regular text
            return [self._create_chunk(
                content=table_text,
                document_id=document_id,
                filename=filename,
                source_url=source_url,
                section_title=section_title,
                section_path=section_path,
                chunk_index=chunk_index,
                document_modified=document_modified,
            )]

        # Find header (first line) and separator (second line with |---|)
        header_line = lines[0]
        separator_idx = 1
        for i, line in enumerate(lines[1:], 1):
            if re.search(r'\|[-:]+\|', line):
                separator_idx = i
                break

        header = '\n'.join(lines[:separator_idx + 1])
        data_rows = lines[separator_idx + 1:]

        if not data_rows:
            return [self._create_chunk(
                content=table_text,
                document_id=document_id,
                filename=filename,
                source_url=source_url,
                section_title=section_title,
                section_path=section_path,
                chunk_index=chunk_index,
                document_modified=document_modified,
            )]

        # Build chunks with header + rows
        current_rows = []
        header_size = len(header) + 1  # +1 for newline

        for row in data_rows:
            row_size = len(row) + 1
            current_size = header_size + sum(len(r) + 1 for r in current_rows)

            if current_size + row_size > self.max_chunk_size and current_rows:
                # Save current chunk
                chunk_content = header + '\n' + '\n'.join(current_rows)
                chunk = self._create_chunk(
                    content=chunk_content,
                    document_id=document_id,
                    filename=filename,
                    source_url=source_url,
                    section_title=section_title,
                    section_path=section_path,
                    chunk_index=chunk_index,
                    document_modified=document_modified,
                )
                chunks.append(chunk)
                chunk_index += 1
                current_rows = [row]
            else:
                current_rows.append(row)

        # Don't forget the last chunk
        if current_rows:
            chunk_content = header + '\n' + '\n'.join(current_rows)
            chunk = self._create_chunk(
                content=chunk_content,
                document_id=document_id,
                filename=filename,
                source_url=source_url,
                section_title=section_title,
                section_path=section_path,
                chunk_index=chunk_index,
                document_modified=document_modified,
            )
            chunks.append(chunk)

        return chunks

    def _split_large_text(
        self,
        text: str,
        document_id: str,
        filename: str,
        source_url: Optional[str],
        section_title: Optional[str],
        section_path: Optional[str],
        start_index: int,
        document_modified: Optional[datetime],
    ) -> list[Chunk]:
        """Split text that's too large for a single chunk by sentences."""
        chunks = []
        chunk_index = start_index

        # Try to split by sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 1 > self.max_chunk_size:
                if current_chunk:
                    chunk = self._create_chunk(
                        content=current_chunk.strip(),
                        document_id=document_id,
                        filename=filename,
                        source_url=source_url,
                        section_title=section_title,
                        section_path=section_path,
                        chunk_index=chunk_index,
                        document_modified=document_modified,
                    )
                    chunks.append(chunk)
                    chunk_index += 1

                    overlap = self._get_overlap(current_chunk)
                    current_chunk = overlap + sentence
                else:
                    # Single sentence too large, just truncate
                    chunk = self._create_chunk(
                        content=sentence[:self.max_chunk_size],
                        document_id=document_id,
                        filename=filename,
                        source_url=source_url,
                        section_title=section_title,
                        section_path=section_path,
                        chunk_index=chunk_index,
                        document_modified=document_modified,
                    )
                    chunks.append(chunk)
                    chunk_index += 1
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence

        if current_chunk.strip():
            chunk = self._create_chunk(
                content=current_chunk.strip(),
                document_id=document_id,
                filename=filename,
                source_url=source_url,
                section_title=section_title,
                section_path=section_path,
                chunk_index=chunk_index,
                document_modified=document_modified,
            )
            chunks.append(chunk)

        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get overlap text from end of previous chunk."""
        if len(text) <= self.overlap_size:
            return ""

        # Try to find a good break point (end of sentence or word)
        overlap = text[-self.overlap_size:]
        space_idx = overlap.find(' ')
        if space_idx > 0:
            overlap = overlap[space_idx + 1:]

        return overlap + " "

    def _create_chunk(
        self,
        content: str,
        document_id: str,
        filename: str,
        source_url: Optional[str],
        section_title: Optional[str],
        section_path: Optional[str],
        chunk_index: int,
        document_modified: Optional[datetime],
    ) -> Chunk:
        """Create a Chunk object with computed ID and metrics."""
        # Generate deterministic chunk ID
        chunk_id = self._generate_chunk_id(document_id, chunk_index, content)

        # Detect content features
        has_table = '|' in content and '---' in content
        has_list = bool(re.search(r'^[-*]\s', content, re.MULTILINE))

        metadata = ChunkMetadata(
            document_id=document_id,
            filename=filename,
            source_url=source_url,
            section_title=section_title,
            section_path=section_path,
            chunk_index=chunk_index,
            has_table=has_table,
            has_list=has_list,
            document_modified=document_modified,
            indexed_at=datetime.now(),
        )

        chunk = Chunk(
            id=chunk_id,
            content=content,
            metadata=metadata,
        )
        chunk.compute_metrics()

        return chunk

    def _generate_chunk_id(self, document_id: str, chunk_index: int, content: str) -> str:
        """Generate a deterministic chunk ID."""
        # Use document ID + index + content hash for uniqueness
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{document_id}_chunk{chunk_index}_{content_hash}"
