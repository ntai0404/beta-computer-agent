"""
interaction/voice/contracts.py

Public data contracts for the Voice Interaction layer.

These types are the boundary between callers (Primary Agent, CLI, future UI)
and the VoiceService. They contain no provider-specific logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Windows SAPI rate range: -10 (slowest) to 10 (fastest), 0 = normal.
RATE_MIN: int = -10
RATE_MAX: int = 10
RATE_DEFAULT: int = 0

VOLUME_MIN: int = 0
VOLUME_MAX: int = 100
VOLUME_DEFAULT: int = 100

# Allowed root directories for audio output (relative to project root).
# Absolute paths are resolved at validation time.
_ALLOWED_OUTPUT_ROOTS: tuple[str, ...] = ("var",)

# ---------------------------------------------------------------------------
# SpeechRequest
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpeechRequest:
    """
    A request for the system to speak a piece of text.

    Callers construct this object. VoiceService validates and fulfils it.
    No provider-specific fields belong here.
    """

    text: str
    """The text to synthesize. Must not be empty."""

    voice_profile_id: Optional[str] = None
    """
    The ID of a voice profile (e.g. 'mambo').
    If None, the provider selects its default.
    """

    language: str = "vi-VN"
    """BCP-47 language tag. Passed as a hint; actual support depends on provider."""

    rate: int = RATE_DEFAULT
    """Speech rate. Windows SAPI range: -10 to +10."""

    volume: int = VOLUME_DEFAULT
    """Volume 0–100."""

    output_path: Optional[Path] = None
    """
    Desired WAV output path. Must be inside var/.
    If None, the provider chooses a unique path under var/artifacts/audio/.
    """

    play_audio: bool = True
    """If True, play the generated audio immediately after synthesis."""

    interruptible: bool = True
    """Reserved for future streaming/interruptible playback support."""

    metadata: dict = field(default_factory=dict)
    """Caller-supplied pass-through metadata attached to the result."""

    def __post_init__(self) -> None:
        _validate_speech_request(self)


def _validate_speech_request(req: SpeechRequest) -> None:
    """Raise ValueError with a clear message if the request is invalid."""
    if not req.text or not req.text.strip():
        raise ValueError("SpeechRequest.text must not be empty.")

    if not (RATE_MIN <= req.rate <= RATE_MAX):
        raise ValueError(
            f"SpeechRequest.rate must be between {RATE_MIN} and {RATE_MAX} "
            f"(Windows SAPI range). Got: {req.rate}"
        )

    if not (VOLUME_MIN <= req.volume <= VOLUME_MAX):
        raise ValueError(
            f"SpeechRequest.volume must be between {VOLUME_MIN} and {VOLUME_MAX}. "
            f"Got: {req.volume}"
        )

    if req.output_path is not None:
        _validate_output_path(req.output_path)


def _validate_output_path(path: Path) -> None:
    """
    Ensure the output path is inside var/ and not inside src/.

    Raises ValueError on violation.
    """
    resolved = path.resolve()
    path_str = str(resolved).replace("\\", "/").lower()

    # Must not be inside src/
    if "/src/" in path_str or path_str.endswith("/src"):
        raise ValueError(
            f"Audio output path must not be inside src/. Got: {resolved}"
        )

    # Must be inside an allowed root (var/)
    parts = resolved.parts
    allowed = any(
        any(p.lower() == root for p in parts)
        for root in _ALLOWED_OUTPUT_ROOTS
    )
    if not allowed:
        raise ValueError(
            f"Audio output path must be inside var/. Got: {resolved}"
        )


# ---------------------------------------------------------------------------
# SpeechArtifact
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpeechArtifact:
    """
    Metadata about an audio file produced by a TTS provider.

    The artifact does not contain the audio bytes — it points to the file path.
    """

    path: Path
    """Absolute path to the WAV file."""

    format: str
    """Audio format, e.g. 'wav'."""

    provider: str
    """Provider ID that produced this artifact, e.g. 'windows-system'."""

    voice_name: Optional[str]
    """The actual voice name used by the provider, or None if unknown."""

    size_bytes: int
    """File size in bytes at the time of creation."""

    created_at: datetime
    """UTC timestamp when the file was written."""

    metadata: dict = field(default_factory=dict)
    """Provider-supplied pass-through metadata."""


# ---------------------------------------------------------------------------
# SpeechResult
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SpeechResult:
    """
    The outcome of a VoiceService.speak() call.

    Contains the original request, the produced artifact, playback status,
    and any non-fatal warnings.
    """

    request: SpeechRequest
    """The original request that produced this result."""

    artifact: SpeechArtifact
    """The audio artifact produced by the TTS provider."""

    played: bool
    """True if the audio was played to the user."""

    duration_ms: Optional[int]
    """Approximate audio duration in milliseconds, or None if unknown."""

    warnings: list[str] = field(default_factory=list)
    """Non-fatal warnings, e.g. voice not found and fallback was used."""
