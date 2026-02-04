#!/usr/bin/env python3
"""Debug EC 7 extraction issues."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import fitz

pdf_path = Path(__file__).parent.parent / "downloads" / "EC 7 Band 1.pdf"

doc = fitz.open(pdf_path)

print(f"Total pages: {len(doc)}")
print(f"Metadata: {doc.metadata}")

# Check pages 5-10 (should have content)
print("\n" + "=" * 70)
print("Checking pages 5-15 for German characters and text quality")
print("=" * 70)

for page_num in range(4, 15):
    page = doc[page_num]
    text = page.get_text("text")

    print(f"\n--- Page {page_num + 1} ---")
    print(f"Length: {len(text)} chars")

    # Check for common German words
    german_words = ["und", "der", "die", "das", "ist", "Norm", "Boden", "Wasser"]
    found_words = [w for w in german_words if w.lower() in text.lower()]
    print(f"German words found: {found_words}")

    # Check for special chars in raw bytes
    text_bytes = text.encode('utf-8', errors='replace')
    has_umlauts = any(c in text for c in 'äöüÄÖÜß')
    print(f"Has umlauts: {has_umlauts}")

    # Show first 300 chars
    sample = text[:300].replace('\n', ' ').strip()
    print(f"Sample: {sample[:100]}...")

    # Check for unusual unicode
    unusual = []
    for c in text[:500]:
        if ord(c) > 127 and c not in 'äöüÄÖÜß':
            unusual.append(f"{c} (U+{ord(c):04X})")
    if unusual:
        unique_unusual = list(set(unusual))[:10]
        print(f"Unusual chars: {unique_unusual}")

doc.close()
