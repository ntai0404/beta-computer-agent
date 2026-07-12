"""
infrastructure/speech/tts/base.py

Abstract TTS provider interface.

VoiceService depends only on this abstraction.
WindowsSystemTtsProvider (and future providers) implement it.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from beta.interaction.voice.contracts import SpeechArtifact, SpeechRequest


@dataclass(frozen=True)
class VoiceInfo:
    """Metadata about a voice available on the current provider."""

    name: str
    """Provider-specific voice name."""

    language: str
    """BCP-47 language tag, e.g. 'vi-VN', 'en-US'."""

    gender: Optional[str] = None
    """'Male', 'Female', or None if unknown."""

    description: Optional[str] = None
    """Human-readable description."""


class TtsProvider(ABC):
    """
    Abstract interface for Text-to-Speech providers.

    Implementations must be stateless between calls or manage their own state
    internally. They receive a SpeechRequest and return a SpeechArtifact.

    VoiceService knows nothing about how synthesis is achieved.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """
        Stable identifier for this provider, e.g. 'windows-system'.
        Used in SpeechArtifact.provider and for logging.
        """

    @abstractmethod
    def synthesize(self, request: SpeechRequest) -> SpeechArtifact:
        """
        Synthesize speech from the given request and return an artifact.

        The returned artifact points to a WAV file on disk.

        Raises:
            TtsProviderError: if synthesis fails for any reason.
            AudioOutputError: if the output file cannot be written.
        """

    @abstractmethod
    def list_voices(self) -> list[VoiceInfo]:
        """
        Return the list of voices available on this provider.

        Returns an empty list if the provider has no installed voices.
        Never raises — if voices cannot be listed, returns [].
        """

    @abstractmethod
    def health_check(self) -> None:
        """
        Verify that the provider is functional.

        Raises TtsProviderError with a diagnostic message if not healthy.
        """
