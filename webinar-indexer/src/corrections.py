"""Post-processing corrections for Whisper transcription errors."""

import re
from pathlib import Path

_DEFAULT_PATH = Path(__file__).resolve().parent.parent / "corrections.tsv"


def load_corrections(path: Path = _DEFAULT_PATH) -> list[tuple[str, str]]:
    """Load correction pairs from a TSV file.

    Returns pairs sorted by descending pattern length (longest first)
    to avoid partial replacements.
    """
    pairs = []
    text = path.read_text(encoding="utf-8")
    for line_num, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t", maxsplit=1)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            pairs.append((parts[0].strip(), parts[1].strip()))
        else:
            print(f"  WARNING: Skipping malformed line {line_num}: {line!r}")
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def apply_corrections(
    text: str, corrections: list[tuple[str, str]]
) -> str:
    """Apply all corrections to text using word-boundary regex."""
    for wrong, right in corrections:
        pattern = r"(?<!\w)" + re.escape(wrong) + r"(?!\w)"
        text, count = re.subn(pattern, right, text, flags=re.IGNORECASE)
        if count > 0:
            print(f"  Corrected '{wrong}' -> '{right}' ({count}x)")
    return text
