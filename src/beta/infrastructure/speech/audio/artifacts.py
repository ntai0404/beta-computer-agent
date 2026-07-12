"""
infrastructure/speech/audio/artifacts.py

Utilities for working with audio artifact files.

Does not contain synthesis or playback logic.
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path


def is_valid_wav(path: Path) -> bool:
    """Return True if the file at path is a readable, non-empty WAV file."""
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with wave.open(str(path), "rb") as wf:
            return wf.getnframes() > 0
    except (wave.Error, EOFError, OSError):
        return False


def wav_duration_ms(path: Path) -> int | None:
    """
    Return the duration of a WAV file in milliseconds.
    Returns None if the file cannot be read.
    """
    try:
        with wave.open(str(path), "rb") as wf:
            frames = wf.getnframes()
            rate = wf.getframerate()
            if rate == 0:
                return None
            return int(frames / rate * 1000)
    except (wave.Error, EOFError, OSError):
        return None
