"""Pinecone Assistant integration for uploading documents."""

import time
import tempfile
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

from pinecone import Pinecone


@dataclass
class UploadResult:
    """Result of a document upload."""
    filename: str
    success: bool
    file_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class UploadStats:
    """Statistics for an upload batch."""
    total: int = 0
    uploaded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class PineconeAssistant:
    """
    Upload documents to Pinecone Assistant.

    The Pinecone Assistant handles chunking, embedding, and indexing internally.
    We upload markdown files with metadata.
    """

    # Rate limits by plan (uploads per minute)
    RATE_LIMITS = {
        "starter": 5,      # 12 sec delay
        "standard": 20,    # 3 sec delay
        "enterprise": 300, # 0.2 sec delay
    }

    def __init__(
        self,
        api_key: str,
        assistant_name: str,
        plan: str = "standard",
    ):
        """
        Initialize the Pinecone Assistant client.

        Args:
            api_key: Pinecone API key
            assistant_name: Name of the assistant to upload to
            plan: Pinecone plan for rate limiting (starter, standard, enterprise)
        """
        self.api_key = api_key
        self.assistant_name = assistant_name
        self.plan = plan

        # Calculate delay between uploads
        uploads_per_minute = self.RATE_LIMITS.get(plan, 20)
        self.upload_delay = 60.0 / uploads_per_minute

        # Initialize client
        self._client: Optional[Pinecone] = None
        self._assistant = None

    def _get_assistant(self):
        """Lazy initialization of Pinecone client and assistant."""
        if self._assistant is None:
            self._client = Pinecone(api_key=self.api_key)
            self._assistant = self._client.assistant.Assistant(
                assistant_name=self.assistant_name
            )
        return self._assistant

    def list_files(self) -> list:
        """
        List all files in the assistant.

        The Pinecone SDK has returned two shapes historically: a response
        object with a `.files` attribute, or a plain list. Handle both.
        """
        assistant = self._get_assistant()
        response = assistant.list_files()
        if hasattr(response, 'files'):
            return response.files
        if isinstance(response, list):
            return response
        return []

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from the assistant.

        Returns True on successful deletion OR if Pinecone reports the file
        was already deleted (404) — the end state is the same. Pinecone's
        list_files endpoint has eventual consistency and occasionally returns
        entries for files that were already removed.
        """
        try:
            assistant = self._get_assistant()
            assistant.delete_file(file_id=file_id)
            return True
        except Exception as e:
            err = str(e)
            # NotFoundException with "already deleted" → treat as success
            if "404" in err and "already deleted" in err.lower():
                return True
            print(f"  Error deleting file {file_id}: {err.splitlines()[0]}")
            return False

    def clear_all_files(self) -> int:
        """
        Delete all files from the assistant.

        Returns:
            Number of files deleted
        """
        files = self.list_files()
        deleted = 0

        print(f"Clearing {len(files)} existing files...")

        for file_info in files:
            file_id = file_info.id if hasattr(file_info, 'id') else file_info.get('id')
            if file_id and self.delete_file(file_id):
                deleted += 1
                print(".", end="", flush=True)

        print(f"\n  Deleted {deleted} files")
        return deleted

    def upload_pdf(
        self,
        pdf_path: Path,
        metadata: Optional[dict] = None,
        multimodal: bool = False,
    ) -> UploadResult:
        """
        Upload a PDF file directly to the assistant.

        Pinecone parses the PDF server-side and preserves page boundaries,
        so context API responses include reference.pages for each snippet.

        Args:
            pdf_path: Path to the .pdf file
            metadata: Optional metadata dict (source_url, title, etc.)
            multimodal: If True, opt into multimodal PDF processing (OCR,
                image captioning). Required for scanned PDFs. Standard plan
                limit: 50 MB / 100 pages per file.

        Returns:
            UploadResult with success status
        """
        pdf_path = Path(pdf_path)
        assistant = self._get_assistant()
        metadata = metadata or {}

        try:
            response = assistant.upload_file(
                file_path=str(pdf_path),
                metadata={
                    "source": metadata.get("source", "sharepoint"),
                    "url": metadata.get("source_url", ""),
                    "filename": pdf_path.name,
                    "title": metadata.get("title", pdf_path.stem),
                },
                multimodal=multimodal,
            )
            file_id = response.id if hasattr(response, "id") else None
            return UploadResult(
                filename=pdf_path.name,
                success=True,
                file_id=file_id,
            )
        except Exception as e:
            return UploadResult(
                filename=pdf_path.name,
                success=False,
                error=str(e),
            )

    def upload_markdown(
        self,
        content: str,
        filename: str,
        metadata: Optional[dict] = None,
    ) -> UploadResult:
        """
        Upload markdown content as a file to the assistant.

        Args:
            content: Markdown content to upload
            filename: Name for the file
            metadata: Optional metadata dict (source_url, etc.)

        Returns:
            UploadResult with success status
        """
        assistant = self._get_assistant()
        metadata = metadata or {}

        # Add metadata header to content
        header_parts = [f"# {metadata.get('title', filename)}"]
        if metadata.get('source_url'):
            header_parts.append(f"\nSource: {metadata['source_url']}")
        header_parts.append(f"\n\n{content}")
        full_content = "\n".join(header_parts)

        # Write to temp file (Pinecone SDK requires file path)
        try:
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.md',
                delete=False,
                encoding='utf-8'
            ) as f:
                f.write(full_content)
                temp_path = f.name

            # Upload to Pinecone
            response = assistant.upload_file(
                file_path=temp_path,
                metadata={
                    "source": metadata.get("source", "sharepoint"),
                    "url": metadata.get("source_url", ""),
                    "filename": filename,
                },
            )

            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)

            file_id = response.id if hasattr(response, 'id') else None
            return UploadResult(
                filename=filename,
                success=True,
                file_id=file_id,
            )

        except Exception as e:
            # Clean up temp file on error
            if 'temp_path' in locals():
                Path(temp_path).unlink(missing_ok=True)

            return UploadResult(
                filename=filename,
                success=False,
                error=str(e),
            )

    def upload_batch(
        self,
        documents: list[dict],
        on_progress: Optional[callable] = None,
    ) -> UploadStats:
        """
        Upload multiple documents with rate limiting.

        Args:
            documents: List of dicts with keys: content, filename, metadata
            on_progress: Optional callback(uploaded, total, current_file)

        Returns:
            UploadStats with counts and errors
        """
        stats = UploadStats(total=len(documents))

        for i, doc in enumerate(documents):
            content = doc.get("content", "")
            filename = doc.get("filename", f"document_{i}.md")
            metadata = doc.get("metadata", {})

            # Progress callback
            if on_progress:
                on_progress(stats.uploaded, stats.total, filename)

            # Upload
            result = self.upload_markdown(content, filename, metadata)

            if result.success:
                stats.uploaded += 1
            else:
                stats.failed += 1
                stats.errors.append(f"{filename}: {result.error}")

            # Rate limiting (skip delay on last item)
            if i < len(documents) - 1:
                time.sleep(self.upload_delay)

        return stats
