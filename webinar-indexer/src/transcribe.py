"""Whisper-based video transcription."""

import os
from pathlib import Path

_model = None


def _load_model():
    global _model
    if _model is None:
        import whisper

        model_name = os.getenv("WHISPER_MODEL", "medium")
        print(f"Loading Whisper model '{model_name}'...")
        _model = whisper.load_model(model_name)
    return _model


def transcribe(video_path: str | Path) -> str:
    """Transcribe a video file to text using Whisper.

    Args:
        video_path: Path to the video file (MP4, etc.)

    Returns:
        The transcribed text.
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    model = _load_model()
    print(f"Transcribing '{video_path.name}'...")
    result = model.transcribe(str(video_path), language="de")
    return result["text"]
