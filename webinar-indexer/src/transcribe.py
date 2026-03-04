"""Whisper-based video transcription."""

import os
from pathlib import Path

_model = None
_device = None


def _load_model():
    global _model, _device
    if _model is None:
        import torch
        import whisper

        if torch.cuda.is_available():
            _device = "cuda"
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"GPU detected: {gpu_name} ({vram_gb:.1f} GB VRAM)")
            print("Using fp16=True, device='cuda'")
        else:
            _device = "cpu"
            print("No GPU detected — using CPU (fp16=False)")

        model_name = os.getenv("WHISPER_MODEL", "medium")
        print(f"Loading Whisper model '{model_name}' on {_device}...")
        _model = whisper.load_model(model_name, device=_device)
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
    fp16 = _device == "cuda"
    print(f"Transcribing '{video_path.name}'...")
    result = model.transcribe(str(video_path), language="de", fp16=fp16)
    return result["text"]
