"""
infrastructure/llm/multimodal/base.py

Abstract interface for multimodal LLM providers used in voice analysis.

Rules:
  - Implementations MUST NOT identify speakers by name or biometric data.
  - Implementations MUST NOT return chain-of-thought in structured output.
  - Implementations MUST check capability before sending media.
  - If a model cannot process audio directly, the caller must use alternatives
    (transcript, extracted frames, audio metadata) and MUST attach a warning.
  - No fake results when capability is missing.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from beta.infrastructure.llm.multimodal.voice_hint_contracts import VoiceHint

MediaType = Literal["audio", "video", "image", "text"]


@dataclass(frozen=True)
class AnalysisCapabilities:
    """
    Declared capabilities of a multimodal provider for voice analysis.

    VoiceHintAnalyzer checks these before sending media.
    If a capability is False, the caller must use a fallback and emit a warning.
    """

    supports_audio_input: bool
    """Can the model receive raw audio as input?"""

    supports_video_input: bool
    """Can the model receive video frames as input?"""

    supports_image_input: bool
    """Can the model receive image frames as input?"""

    supports_transcription: bool
    """Can the model produce a transcript from audio/video?"""

    supports_structured_output: bool
    """Can the model return structured JSON (not just prose)?"""

    max_audio_duration_seconds: Optional[float] = None
    """Maximum supported audio duration; None means unknown."""

    max_file_size_bytes: Optional[int] = None
    """Maximum supported file size; None means unknown."""

    supported_audio_formats: list[str] = field(default_factory=list)
    """e.g. ['wav', 'mp3', 'ogg']"""

    supported_video_formats: list[str] = field(default_factory=list)
    """e.g. ['mp4', 'webm']"""

    notes: str = ""
    """Human-readable notes about limitations."""


@dataclass
class AnalysisRequest:
    """
    A request to analyze a voice reference file.
    """

    reference_path: Path
    """Local path to the audio or video file."""

    character_profile_id: str
    """The profile ID this analysis is for (e.g. 'mambo')."""

    persona_alias: str
    """Display alias (e.g. 'Mambo')."""

    existing_transcript: Optional[str] = None
    """Pre-existing transcript to pass to the model (reduces need for audio input)."""

    language_hint: Optional[str] = None
    """BCP-47 language hint for the reference audio."""

    additional_context: Optional[str] = None
    """Optional context about the source (game, scene, emotion category)."""


@dataclass
class AnalysisResult:
    """
    Raw result from a multimodal analysis call.

    The VoiceHintAnalyzer post-processes this into a VoiceHint.
    """

    voice_hint: VoiceHint
    """The populated (or partially populated) VoiceHint."""

    provider_id: str
    """Which provider performed this analysis."""

    raw_response_summary: Optional[str] = None
    """
    A brief summary of the provider response for logging.
    MUST NOT contain chain-of-thought or private reasoning.
    MUST NOT contain the full model response.
    """

    fallbacks_used: list[str] = field(default_factory=list)
    """List of fallback strategies used when direct audio was not supported."""


class MultimodalVoiceAnalyzer(ABC):
    """
    Abstract interface for voice reference analysis via multimodal LLM.

    Implementations:
      - Must not identify speakers by name.
      - Must not return chain-of-thought.
      - Must check capabilities before sending media.
      - Must return warnings when analysis is limited.
      - Must not produce fake results when data is insufficient.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Stable provider identifier."""

    @abstractmethod
    def capabilities(self) -> AnalysisCapabilities:
        """Return declared capabilities of this provider."""

    @abstractmethod
    def analyze_audio(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Analyze a voice reference audio file.

        If the provider does not support audio input, implementations must:
          1. Check capabilities() first.
          2. Use fallback (transcript, metadata) if audio is unsupported.
          3. Populate result.fallbacks_used with the fallback strategy.
          4. Add a warning to the VoiceHint.
          5. NEVER send audio to a model that does not support it.
          6. NEVER return a fake result.

        Raises:
            NotImplementedError: if this provider has no audio analysis capability
                                 and no fallback is possible.
        """

    @abstractmethod
    def analyze_video(self, request: AnalysisRequest) -> AnalysisResult:
        """
        Analyze a voice reference video file.

        Same fallback rules as analyze_audio apply.
        """

    @abstractmethod
    def transcribe(self, request: AnalysisRequest) -> Optional[str]:
        """
        Produce a transcript from the reference audio or video.

        Returns None if transcription is not supported or not possible.
        Never raises — adds warnings to the result instead.
        """

    @abstractmethod
    def health_check(self) -> None:
        """
        Verify that the provider is reachable and configured.

        Raises an appropriate exception if not healthy.
        """

    @abstractmethod
    def supported_media_types(self) -> list[MediaType]:
        """Return the list of media types this provider can process."""
