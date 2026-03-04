#!/usr/bin/env python3
"""Batch-transcribe all videos in videos/ folder."""

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


def slugify(name: str) -> str:
    """Convert a filename to a URL-friendly slug."""
    return name.lower().replace(" ", "-")


def main():
    videos_dir = PROJECT_ROOT / "videos"
    if not videos_dir.is_dir():
        print(f"Videos directory not found: {videos_dir}")
        sys.exit(1)

    raw_dir = PROJECT_ROOT / "transcripts" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    video_files = sorted(videos_dir.glob("*.mp4"))
    if not video_files:
        print("No .mp4 files found in videos/")
        sys.exit(0)

    corrections = load_corrections()
    print(f"Found {len(video_files)} video(s), {len(corrections)} correction rules\n")

    skipped = 0
    processed = 0
    errors = 0

    for i, video_path in enumerate(video_files, 1):
        slug = slugify(video_path.stem)
        raw_path = raw_dir / f"{slug}.txt"

        if raw_path.exists():
            print(f"[{i}/{len(video_files)}] SKIP (exists): {video_path.name}")
            skipped += 1
            continue

        print(f"[{i}/{len(video_files)}] Transcribing: {video_path.name}")
        try:
            transcript = transcribe(video_path)
            print("  Applying corrections...")
            transcript = apply_corrections(transcript, corrections)
            raw_path.write_text(transcript, encoding="utf-8")
            print(f"  -> Saved: {raw_path.name}")
            processed += 1
        except Exception as e:
            print(f"  ERROR ({type(e).__name__}): {e}")
            errors += 1

    print(f"\nDone. Processed: {processed}, Skipped: {skipped}, Errors: {errors}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
