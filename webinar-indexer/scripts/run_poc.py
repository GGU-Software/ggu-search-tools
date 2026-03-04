#!/usr/bin/env python3
"""POC: Video -> Transkript -> strukturiertes Markdown."""

import os
import sys
from pathlib import Path

# Allow running from project root or scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure ffmpeg is findable (winget installs to a non-PATH location)
_ffmpeg_dirs = list(Path.home().glob(
    "AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg*/ffmpeg-*/bin"
))
if _ffmpeg_dirs:
    os.environ["PATH"] = str(_ffmpeg_dirs[0]) + os.pathsep + os.environ.get("PATH", "")

from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")

from src.transcribe import transcribe
from src.corrections import load_corrections, apply_corrections
from src.structure import structure


def slugify(name: str) -> str:
    """Convert a filename to a URL-friendly slug."""
    return name.lower().replace(" ", "-")


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_poc.py <video-path>")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    if not video_path.is_absolute():
        video_path = PROJECT_ROOT / video_path

    slug = slugify(video_path.stem)
    raw_dir = PROJECT_ROOT / "transcripts" / "raw"
    structured_dir = PROJECT_ROOT / "transcripts" / "structured"
    raw_dir.mkdir(parents=True, exist_ok=True)
    structured_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Transcribe + correct
    raw_path = raw_dir / f"{slug}.txt"
    if raw_path.exists():
        print(f"Raw transcript already exists: {raw_path}")
        transcript = raw_path.read_text(encoding="utf-8")
    else:
        transcript = transcribe(video_path)
        corrections = load_corrections()
        print("Applying corrections...")
        transcript = apply_corrections(transcript, corrections)
        raw_path.write_text(transcript, encoding="utf-8")
        print(f"Raw transcript saved: {raw_path}")

    # Step 2: Structure
    structured_path = structured_dir / f"{slug}.md"
    print("Structuring transcript with Claude...")
    markdown = structure(transcript, video_path.name)
    structured_path.write_text(markdown, encoding="utf-8")
    print(f"Structured document saved: {structured_path}")

    print("\nDone! Review the output:")
    print(f"  Raw:        {raw_path}")
    print(f"  Structured: {structured_path}")


if __name__ == "__main__":
    main()
