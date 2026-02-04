#!/usr/bin/env python3
"""
Fetch the 3 specific test documents from SharePoint.
Downloads them to downloads/ folder for processing.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.sharepoint import SharePointClient, fetch_documents


async def fetch_test_documents():
    """Fetch and download the test documents."""

    # Load test document config
    config_path = Path(__file__).parent.parent / "test_documents.json"
    with open(config_path, encoding="utf-8") as f:
        test_docs = json.load(f)

    # Create target filenames set for matching
    target_files = {doc["filename"] for doc in test_docs}

    print(f"Looking for {len(target_files)} specific documents:")
    for doc in test_docs:
        print(f"  - {doc['short_name']}")
    print()

    # Initialize client
    client = SharePointClient()
    if not await client.initialize():
        print("ERROR: Failed to initialize SharePoint client")
        return

    # Create downloads directory
    downloads_dir = Path(__file__).parent.parent / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    # Search and download
    found = []
    scanned = 0

    print("Scanning SharePoint...")
    async for doc in fetch_documents(client):
        scanned += 1
        if scanned % 1000 == 0:
            print(f"  ... scanned {scanned} documents, found {len(found)}/{len(target_files)}")

        if doc.filename in target_files:
            print(f"\nFOUND: {doc.filename}")
            print(f"  Path: {doc.parent_path}")
            print(f"  Size: {doc.size // 1024} KB")

            # Download the document
            print(f"  Downloading...")
            content = await client.download_file(doc.id)

            if content:
                # Save to downloads folder
                safe_filename = doc.filename.replace("/", "_").replace("\\", "_")
                output_path = downloads_dir / safe_filename
                output_path.write_bytes(content)
                print(f"  Saved to: {output_path}")

                found.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "local_path": str(output_path),
                    "web_url": doc.web_url,
                    "size": doc.size,
                    "etag": doc.etag,
                    "parent_path": doc.parent_path,
                })
            else:
                print(f"  ERROR: Download failed!")

            # Stop early if we found all
            if len(found) == len(target_files):
                break

    await client.close()

    print("\n" + "=" * 60)
    print(f"Found and downloaded {len(found)}/{len(target_files)} documents")

    # Save metadata
    metadata_path = downloads_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(found, f, indent=2, ensure_ascii=False)
    print(f"Metadata saved to: {metadata_path}")

    return found


if __name__ == "__main__":
    asyncio.run(fetch_test_documents())
