#!/usr/bin/env python3
"""
Find specific test documents in SharePoint.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.sharepoint import SharePointClient, fetch_documents

# Test documents to find
TEST_PATTERNS = [
    "DIN 4023",
    "EC 7 Band 1",
    "DIN EN ISO 17892-1",
]


async def find_test_documents():
    """Find the specific test documents."""
    client = SharePointClient()
    if not await client.initialize():
        print("Failed to initialize client")
        return

    print("Searching for test documents...")
    print("=" * 70)

    found = {p: [] for p in TEST_PATTERNS}
    total_scanned = 0

    async for doc in fetch_documents(client):
        total_scanned += 1
        if total_scanned % 500 == 0:
            print(f"  ... scanned {total_scanned} documents")

        filename_lower = doc.filename.lower()
        for pattern in TEST_PATTERNS:
            if pattern.lower() in filename_lower:
                found[pattern].append(doc)

    await client.close()

    print("=" * 70)
    print(f"Scanned {total_scanned} documents total\n")

    # Show results
    all_matches = []
    for pattern, docs in found.items():
        print(f"\n{pattern}:")
        print("-" * 40)
        if docs:
            for doc in docs:
                print(f"  {doc.filename}")
                print(f"    Path: {doc.parent_path}")
                print(f"    Size: {doc.size // 1024} KB")
                print(f"    ID: {doc.id}")
                all_matches.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "web_url": doc.web_url,
                    "parent_path": doc.parent_path,
                    "size": doc.size,
                    "etag": doc.etag,
                })
        else:
            print("  (not found)")

    # Save matches to JSON for later use
    output_path = Path(__file__).parent.parent / "test_documents.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_matches, f, indent=2, ensure_ascii=False)

    print(f"\n\nSaved {len(all_matches)} documents to {output_path}")
    return all_matches


if __name__ == "__main__":
    asyncio.run(find_test_documents())
