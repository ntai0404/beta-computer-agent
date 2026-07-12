"""
infrastructure/speech/tts/voice_conversion_base.py

Abstract interface for Voice Conversion (RVC and equivalent) providers.

CRITICAL DISTINCTION:
  TtsProvider   : text   → audio  (synthesis)
  VoiceConversionProvider: audio → audio  (timbre conversion)

These are DIFFERENT providers with DIFFERENT interfaces.
Do NOT conflate them into a single "voice model" concept.

RVC pipeline:
  Text → TtsProvider → source audio → VoiceConversionProvider → character-like audio

Direct Character TTS pipeline (future):
  Text → CharacterTtsProvider → character-like audio

This file defines the VoiceConversionProvider abstraction only.
No implementation is included in this milestone.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class VoiceConversionModelInfo:
    """Metadata about a loaded voice conversion model."""

    model_id: str
    """Stable identifier for this model."""

    character_profile_id: str
    """The profile ID this model is trained for (e.g. 'mambo')."""

    canonical_character_id: Optional[str]
    """Canonical source character ID, or None if unresolved."""

    model_format: str
    """e.g. 'rvc-v2', 'so-vits-svc', etc."""

    sample_rate: int
    """Expected input and output sample rate in Hz."""

    model_path: Path
    """Path to the model weights file."""

    index_path: Optional[Path]
    """Path to the feature index file (required by RVC)."""

    license: Optional[str]
    """License statement for this model."""


@dataclass
class VoiceConversionRequest:
    """A request to convert source audio to target character timbre."""

    source_audio_path: Path
    """Path to the source WAV file (output from TtsProvider)."""

    output_path: Optional[Path] = None
    """Desired output path. If None, provider chooses a unique path."""

    pitch_shift_semitones: int = 0
    """Pitch shift in semitones (0 = no shift)."""

    f0_method: str = "dio"
    """Pitch extraction method: 'dio', 'harvest', 'pm', 'crepe'."""

    filter_radius: int = 3
    """Median filter radius for smoothing."""

    index_rate: float = 0.75
    """Feature index rate (0.0 to 1.0). Higher = more character."""

    rms_mix_rate: float = 0.25
    """RMS normalization mix rate."""

    protect: float = 0.33
    """Protection for unvoiced consonants."""

    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


@dataclass(frozen=True)
class VoiceConversionArtifact:
    """The result of a voice conversion operation."""

    path: Path
    """Path to the converted WAV file."""

    source_path: Path
    """Path to the source audio that was converted."""

    model_id: str
    """Which model was used."""

    character_profile_id: str
    """Which character profile this conversion was for."""

    size_bytes: int
    """File size in bytes."""

    sample_rate: int
    """Sample rate of the output file."""

    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})


class VoiceConversionProvider(ABC):
    """
    Abstract interface for Voice Conversion providers (RVC, SoVITS, etc.).

    Input:  source audio (WAV produced by a TtsProvider)
    Output: converted audio (WAV with target character timbre)

    NOT a TtsProvider. Does NOT accept text as input.
    """

    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Stable provider identifier."""

    @abstractmethod
    def load_model(self, model_info: VoiceConversionModelInfo) -> None:
        """
        Load the voice conversion model.

        Raises an appropriate error if the model file does not exist or is
        incompatible with this provider.
        """

    @abstractmethod
    def convert(
        self, request: VoiceConversionRequest
    ) -> VoiceConversionArtifact:
        """
        Convert source audio to the target character timbre.

        The source audio must already exist on disk (produced by TtsProvider).

        Raises:
            ValueError: if source_audio_path does not exist.
            RuntimeError: if the model is not loaded.
            VoiceConversionError: if conversion fails.
        """

    @abstractmethod
    def health_check(self) -> None:
        """Verify the provider and model are functional."""

    @abstractmethod
    def model_info(self) -> Optional[VoiceConversionModelInfo]:
        """Return info about the currently loaded model, or None."""
