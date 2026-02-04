"""
Document fetching from SharePoint.

Provides recursive document listing with pagination support.
"""

import logging
from datetime import datetime
from typing import AsyncGenerator, Optional
from collections import deque

from src.sharepoint.client import SharePointClient
from src.sharepoint.models import SharePointDocument, DocumentType, FolderInfo
from src.config import get_settings

logger = logging.getLogger(__name__)


def parse_datetime(value: str) -> datetime:
    """Parse ISO 8601 datetime string from Graph API."""
    # Handle 'Z' suffix (UTC)
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def parse_document(item: dict) -> Optional[SharePointDocument]:
    """
    Parse a Graph API item into a SharePointDocument.

    Args:
        item: Raw item from Graph API response.

    Returns:
        SharePointDocument or None if parsing fails.
    """
    try:
        # Only process files (not folders)
        if "file" not in item:
            return None

        filename = item["name"]

        # Extract author names safely
        created_by = None
        if "createdBy" in item and "user" in item["createdBy"]:
            created_by = item["createdBy"]["user"].get("displayName")

        modified_by = None
        if "lastModifiedBy" in item and "user" in item["lastModifiedBy"]:
            modified_by = item["lastModifiedBy"]["user"].get("displayName")

        # Extract parent path
        parent_path = ""
        if "parentReference" in item:
            parent_path = item["parentReference"].get("path", "")
            # Remove drive prefix (e.g., /drives/{id}/root:)
            if ":/" in parent_path:
                parent_path = parent_path.split(":/", 1)[1]

        return SharePointDocument(
            id=item["id"],
            filename=filename,
            web_url=item.get("webUrl", ""),
            download_url=item.get("@microsoft.graph.downloadUrl"),
            size=item.get("size", 0),
            etag=item.get("eTag", ""),
            mime_type=item.get("file", {}).get("mimeType"),
            document_type=DocumentType.from_filename(filename),
            created_at=parse_datetime(item["createdDateTime"]),
            modified_at=parse_datetime(item["lastModifiedDateTime"]),
            created_by=created_by,
            modified_by=modified_by,
            parent_path=parent_path,
        )

    except Exception as e:
        logger.warning(f"Failed to parse document: {e}")
        return None


async def fetch_documents(
    client: SharePointClient,
    folder: Optional[str] = None,
    file_extensions: Optional[list[str]] = None,
) -> AsyncGenerator[SharePointDocument, None]:
    """
    Fetch all documents from SharePoint folder recursively.

    Uses queue-based iteration (not recursion) to avoid stack overflow.
    Handles pagination via @odata.nextLink.

    Args:
        client: Initialized SharePointClient.
        folder: Folder path to start from. Defaults to configured folder.
        file_extensions: Filter by extensions (e.g., [".pdf"]). None = all files.

    Yields:
        SharePointDocument for each matching file.
    """
    settings = get_settings()
    folder = folder or settings.sharepoint_folder
    file_extensions = file_extensions or settings.supported_extensions
    max_depth = settings.max_folder_depth

    # Ensure client is ready
    await client.ensure_valid_token()

    session = await client.get_session()
    headers = client.get_auth_headers()

    # Start URL for the root folder
    start_url = (
        f"{client.GRAPH_API_BASE}/drives/{client.drive_id}/root:/{folder}:/children"
    )

    # Queue of folders to process: (url, depth)
    folder_queue: deque[FolderInfo] = deque()
    folder_queue.append(FolderInfo(
        id="root",
        name=folder,
        url=start_url,
        depth=0
    ))

    total_files = 0
    total_folders = 0

    while folder_queue:
        current_folder = folder_queue.popleft()

        if current_folder.depth > max_depth:
            logger.warning(
                f"Max depth ({max_depth}) reached, skipping: {current_folder.name}"
            )
            continue

        logger.debug(f"Processing folder: {current_folder.name} (depth={current_folder.depth})")

        # Paginate through folder contents
        next_url: Optional[str] = current_folder.url

        while next_url:
            async with session.get(next_url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to list folder {current_folder.name}: "
                        f"{response.status} - {error_text}"
                    )
                    break

                data = await response.json()
                items = data.get("value", [])

                for item in items:
                    # Handle folders - add to queue
                    if "folder" in item:
                        total_folders += 1
                        subfolder_url = (
                            f"{client.GRAPH_API_BASE}/drives/{client.drive_id}"
                            f"/items/{item['id']}/children"
                        )
                        folder_queue.append(FolderInfo(
                            id=item["id"],
                            name=item["name"],
                            url=subfolder_url,
                            depth=current_folder.depth + 1
                        ))
                        logger.debug(f"  Found subfolder: {item['name']}")

                    # Handle files
                    elif "file" in item:
                        # Check extension filter
                        filename = item["name"]
                        if file_extensions:
                            ext = "." + filename.lower().split(".")[-1] if "." in filename else ""
                            if ext not in file_extensions:
                                continue

                        doc = parse_document(item)
                        if doc:
                            total_files += 1
                            yield doc

                # Get next page URL
                next_url = data.get("@odata.nextLink")

    logger.info(f"Finished: {total_files} files, {total_folders} subfolders processed")


async def count_documents(
    client: SharePointClient,
    folder: Optional[str] = None,
    file_extensions: Optional[list[str]] = None,
) -> dict:
    """
    Count documents without fetching all metadata.

    Args:
        client: Initialized SharePointClient.
        folder: Folder path to start from.
        file_extensions: Filter by extensions.

    Returns:
        Dict with counts: total_files, total_folders, by_type.
    """
    counts = {
        "total_files": 0,
        "total_folders": 0,
        "by_type": {},
    }

    async for doc in fetch_documents(client, folder, file_extensions):
        counts["total_files"] += 1
        doc_type = doc.document_type.value
        counts["by_type"][doc_type] = counts["by_type"].get(doc_type, 0) + 1

    return counts
