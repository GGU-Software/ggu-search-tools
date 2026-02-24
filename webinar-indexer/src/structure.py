"""Claude-based transcript structuring."""

import os

import anthropic

from .prompts import STRUCTURE_PROMPT


def structure(transcript: str, source_filename: str) -> str:
    """Structure a raw transcript into a Markdown document using Claude.

    Args:
        transcript: Raw transcript text.
        source_filename: Original video filename (for context).

    Returns:
        Structured Markdown string.
    """
    client = anthropic.Anthropic()  # uses ANTHROPIC_API_KEY env var

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": (
                    f"{STRUCTURE_PROMPT}\n\n"
                    f"Quelldatei: {source_filename}\n\n"
                    f"--- TRANSKRIPT ---\n\n{transcript}"
                ),
            }
        ],
    )

    return message.content[0].text
