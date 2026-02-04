#!/usr/bin/env python3
"""
Search for documents in SharePoint by name pattern.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.sharepoint import SharePointClient, fetch_documents


async def search_documents(pattern: str, max_results: int = 20):
    """Search for documents matching a pattern."""
    pattern_lower = pattern.lower()

    client = SharePointClient()
    if not await client.initialize():
        print("Failed to initialize client")
        return

    print(f"Searching for: {pattern}")
    print("-" * 70)

    matches = []
    async for doc in fetch_documents(client):
        if pattern_lower in doc.filename.lower():
            matches.append(doc)
            print(f"[{len(matches)}] {doc.filename}")
            print(f"    Path: {doc.parent_path}")
            print(f"    Size: {doc.size // 1024} KB")
            print(f"    URL: {doc.web_url}")
            print()

            if len(matches) >= max_results:
                print(f"... stopped at {max_results} results")
                break

    await client.close()

    print("-" * 70)
    print(f"Found {len(matches)} documents matching '{pattern}'")
    return matches


if __name__ == "__main__":
    pattern = sys.argv[1] if len(sys.argv) > 1 else "DIN 4023"
    asyncio.run(search_documents(pattern))
