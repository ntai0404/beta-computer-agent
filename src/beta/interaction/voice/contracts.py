"""
interaction/voice/contracts.py

Core contracts for the Beta Voice Engine.
Defines abstractions for TTS, Voice Conversion, and Playback.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


class ReadinessStatus(str, enum.Enum):
    FALLBACK_READY = "fallback_ready"
    CONVERSION_CANDIDATE = "conversion_candidate"
    CONVERSION_READY = "conversion_ready"
    DIRECT_TTS_CANDIDATE = "direct_tts_candidate"
    DIRECT_TTS_READY = "direct_tts_ready"
    BLOCKED = "blocked"
    UNRESOLVED = "unresolved"


class PipelinePreference(str, enum.Enum):
    AUTO = "auto"
    SYSTEM_TTS = "system_tts"
    BASE_TTS_ONLY = "base_tts_only"
    BASE_TTS_PLUS_CONVERSION = "base_tts_plus_conversion"
    DIRECT_CHARACTER_TTS = "direct_character_tts"


@dataclass
class VoiceHint:
    speaking_rate: float | None = None
    volume: float | None = None
    installed_voice_preference: str | None = None
    style_metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ResolvedVoiceProfile:
    profile_id: str
    character_profile_id: str
    persona_alias: str
    canonical_identity_status: str
    selected_pipeline: PipelinePreference
    selected_tts_provider: str
    selected_conversion_provider: str | None
    selected_voice_name: str | None
    voice_hint: VoiceHint | None
    model_paths: dict[str, str]
    provenance: dict[str, str]
    warnings: list[str]
    readiness_status: ReadinessStatus


@dataclass
class SpeechRequest:
    text: str
    character_profile_id: str
    language: str = "vi-VN"
    rate: float = 1.0
    volume: float = 1.0
    play_audio: bool = True
    output_path: Path | None = None
    pipeline_preference: PipelinePreference = PipelinePreference.AUTO
    allow_untrusted_model: bool = False
    metadata: dict = field(default_factory=dict)


@dataclass
class SpeechArtifact:
    path: Path
    format: str
    sample_rate: int
    channels: int
    provider: str
    pipeline: str
    character_profile_id: str
    generated_at: str
    size_bytes: int
    checksum: str
    provenance: str
    warnings: list[str]


@dataclass
class VoicePipelineResult:
    request: SpeechRequest
    resolved_profile: ResolvedVoiceProfile
    intermediate_artifacts: list[SpeechArtifact]
    final_artifact: SpeechArtifact | None
    played: bool
    warnings: list[str]
    pipeline_trace: list[str]


class TtsProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def synthesize(self, text: str, hint: VoiceHint | None, output_path: Path) -> SpeechArtifact:
        """Synthesize text to audio and return the artifact."""
        ...


class VoiceConversionProvider(Protocol):
    @property
    def provider_id(self) -> str: ...

    def inspect_model(self, metadata_only: bool = True) -> dict:
        """Inspect the model without loading it into memory (unless metadata_only=False and trusted)."""
        ...

    def convert(self, source_audio: Path, target_profile: ResolvedVoiceProfile, output_path: Path) -> SpeechArtifact:
        """Convert source audio to target voice."""
        ...

    def health_check(self) -> bool: ...

    def capabilities(self) -> dict: ...


class AudioPlayer(Protocol):
    def play(self, audio_path: Path) -> bool:
        """Play the audio file synchronously."""
        ...


class VoiceHintAnalyzer(Protocol):
    def analyze(self, reference_audio: Path) -> VoiceHint:
        """Analyze reference audio to generate a structured VoiceHint."""
        ...
