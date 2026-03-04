#!/usr/bin/env python3
"""Batch-structure all raw transcripts that lack structured versions."""

import sys
from pathlib import Path

# Allow running from project root or scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.structure import structure


def main():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set. Check .env file.")
        sys.exit(1)

    raw_dir = PROJECT_ROOT / "transcripts" / "raw"
    structured_dir = PROJECT_ROOT / "transcripts" / "structured"
    structured_dir.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(raw_dir.glob("*.txt"))
    if not raw_files:
        print("No raw transcripts found.")
        sys.exit(0)

    print(f"Found {len(raw_files)} raw transcript(s)\n")

    skipped = 0
    processed = 0
    errors = 0

    for i, raw_path in enumerate(raw_files, 1):
        structured_path = structured_dir / f"{raw_path.stem}.md"

        if structured_path.exists():
            print(f"[{i}/{len(raw_files)}] SKIP (exists): {raw_path.name}")
            skipped += 1
            continue

        print(f"[{i}/{len(raw_files)}] Structuring: {raw_path.name}")
        transcript = raw_path.read_text(encoding="utf-8")
        source_name = raw_path.stem.replace("-", " ").title() + ".mp4"

        try:
            markdown = structure(transcript, source_name)
            structured_path.write_text(markdown, encoding="utf-8")
            print(f"  -> Saved: {structured_path.name}")
            processed += 1
        except Exception as e:
            print(f"  ERROR ({type(e).__name__}): {e}")
            errors += 1

    print(f"\nDone. Processed: {processed}, Skipped: {skipped}, Errors: {errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
