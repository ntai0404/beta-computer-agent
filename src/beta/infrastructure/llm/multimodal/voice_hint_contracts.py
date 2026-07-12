"""
infrastructure/llm/multimodal/voice_hint_contracts.py

Provider-neutral Voice Hint schema.

A Voice Hint is a structured metadata document produced by multimodal
analysis of a voice reference (audio or video). It describes speaking style,
prosody, and audio quality — it is NOT a voice model, embedding, or clone.

Rules:
  - canonical_identity_status must be 'unresolved' until externally verified.
  - chain-of-thought MUST NOT be stored here.
  - raw secrets or credentials MUST NOT appear in any field.
  - The hint does not identify the speaker by name or by biometric data.
  - The hint does not claim to reproduce a specific person's voice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional


# Possible values for canonical identity resolution status.
CanonicalIdentityStatus = Literal[
    "unresolved",   # not yet verified from a canonical source
    "resolved",     # confirmed from game/package metadata
    "disputed",     # conflicting information from multiple sources
]

# Possible values for individual field confidence.
ObservationStatus = Literal[
    "directly_observed",
    "inferred",
    "unknown",
]

# Overall analysis confidence level.
ConfidenceLevel = Literal["high", "medium", "low", "insufficient_data"]


@dataclass
class SourceReference:
    """A reference to a specific audio or video clip used during analysis."""

    path: str
    """Local file path (relative to project root or absolute)."""

    sha256: Optional[str] = None
    """SHA-256 hash of the file at analysis time."""

    duration_seconds: Optional[float] = None
    """Duration of the clip in seconds."""

    media_type: Optional[str] = None
    """MIME type, e.g. 'audio/wav', 'video/mp4'."""

    scene_or_category: Optional[str] = None
    """Game scene, event, or emotional category if known."""


@dataclass
class AudioQualityAssessment:
    """Quality assessment of the reference audio."""

    background_noise: ObservationStatus = "unknown"
    """Presence of background noise."""

    background_music: ObservationStatus = "unknown"
    """Presence of background music."""

    multiple_speakers: ObservationStatus = "unknown"
    """Whether more than one speaker is audible."""

    sound_effects: ObservationStatus = "unknown"
    """Presence of sound effects over the voice."""

    compression_artifacts: ObservationStatus = "unknown"
    """Noticeable audio compression artifacts."""

    sufficient_for_cloning: bool = False
    """Whether the clip meets minimum quality for voice model training."""

    sufficient_for_analysis: bool = False
    """Whether the clip is usable for style analysis."""

    warnings: list[str] = field(default_factory=list)
    """Specific quality warnings for this clip."""


@dataclass
class SpeakingStyleHint:
    """
    Provider-neutral description of speaking style.

    All fields are optional — analysis may not determine every dimension.
    Field values are descriptive strings, not numeric scores (unless noted).
    """

    # --- Prosody ---
    speaking_rate: Optional[str] = None
    """e.g. 'slow', 'normal', 'fast', 'very fast'."""

    speaking_rate_status: ObservationStatus = "unknown"

    pitch_tendency: Optional[str] = None
    """e.g. 'high', 'mid-high', 'mid', 'low'."""

    pitch_tendency_status: ObservationStatus = "unknown"

    energy: Optional[str] = None
    """e.g. 'high energy', 'moderate', 'calm', 'whispered'."""

    energy_status: ObservationStatus = "unknown"

    rhythm: Optional[str] = None
    """e.g. 'staccato', 'flowing', 'irregular', 'steady'."""

    rhythm_status: ObservationStatus = "unknown"

    pause_style: Optional[str] = None
    """e.g. 'frequent short pauses', 'long dramatic pauses', 'minimal pauses'."""

    pause_style_status: ObservationStatus = "unknown"

    # --- Expression ---
    expressiveness: Optional[str] = None
    """e.g. 'highly expressive', 'moderate', 'flat', 'theatrical'."""

    emotional_tone: Optional[str] = None
    """e.g. 'cheerful', 'confident', 'warm', 'neutral', 'melancholic'."""

    conversational_attitude: Optional[str] = None
    """e.g. 'friendly', 'formal', 'playful', 'earnest'."""

    # --- Timbre ---
    timbre_descriptors: list[str] = field(default_factory=list)
    """e.g. ['bright', 'resonant', 'breathy', 'nasal']. Purely descriptive."""

    # --- Pronunciation ---
    pronunciation_notes: Optional[str] = None
    """Notes on accent, dialect, or distinctive pronunciation patterns."""

    language: Optional[str] = None
    """BCP-47 language tag of the speech in the reference, e.g. 'ja-JP'."""

    # --- Style summary ---
    style_prompt: Optional[str] = None
    """
    A short, plain-language description of the speaking style for use as a
    TTS/voice model style hint. Must NOT identify the speaker by name.
    e.g. 'Upbeat, high-pitched, energetic delivery with expressive emphasis.'
    """


@dataclass
class VoiceHint:
    """
    Provider-neutral Voice Hint document.

    Produced by multimodal analysis of voice references.
    Describes speaking style and audio quality.
    Does NOT contain voice model weights, embeddings, or speaker identity claims.

    Storage location: profiles/characters/<profile_id>/voice-hint.json
    (when populated)
    """

    # --- Identity ---
    profile_id: str
    """Stable profile ID, e.g. 'mambo'. Never changes once assigned."""

    persona_alias: str
    """User-facing display name, e.g. 'Mambo'."""

    canonical_character_id: Optional[str] = None
    """
    Canonical character ID from the source (game, package, etc.).
    Must be None until externally verified.
    """

    canonical_character_name: Optional[str] = None
    """
    Canonical character name from the source.
    Must be None until externally verified.
    """

    canonical_identity_status: CanonicalIdentityStatus = "unresolved"
    """Always 'unresolved' until verified from a canonical source."""

    # --- Sources ---
    source_references: list[SourceReference] = field(default_factory=list)
    """The audio/video clips used for this analysis."""

    # --- Transcript ---
    transcript: Optional[str] = None
    """Transcript of the reference audio, if available."""

    transcript_language: Optional[str] = None
    """BCP-47 language of the transcript."""

    transcript_confidence: ConfidenceLevel = "insufficient_data"

    # --- Style ---
    style: SpeakingStyleHint = field(default_factory=SpeakingStyleHint)

    # --- Quality ---
    audio_quality: list[AudioQualityAssessment] = field(default_factory=list)
    """One quality assessment per source reference."""

    # --- Analysis metadata ---
    analysis_provider: Optional[str] = None
    """Which provider performed the analysis, e.g. 'gemini-pro-vision'."""

    analysis_model: Optional[str] = None
    """Specific model used."""

    analyzed_at: Optional[datetime] = None
    """UTC timestamp of analysis."""

    overall_confidence: ConfidenceLevel = "insufficient_data"
    """Confidence in the style analysis as a whole."""

    warnings: list[str] = field(default_factory=list)
    """
    Non-fatal warnings from analysis:
    - clip too short
    - background music detected
    - multiple speakers detected
    - heavy compression
    - transcript uncertain
    - audio insufficient for cloning/training
    etc.
    """

    version: int = 1
    """Monotonically increasing version. Increment on update."""

    metadata: dict = field(default_factory=dict)
    """Provider pass-through metadata. No secrets."""

    def is_ready_for_provider_mapping(self) -> bool:
        """
        Return True if this hint contains enough information to attempt
        mapping to a TTS provider.
        """
        return (
            self.overall_confidence in ("high", "medium")
            and self.style.style_prompt is not None
        )

    def windows_tts_mapping(self) -> dict:
        """
        Extract the subset of hints that Windows System TTS can use.

        Returns a dict with keys: rate (int | None), volume (int | None),
        voice_name_hint (str | None), warnings (list[str]).

        Windows TTS CANNOT reproduce: timbre, emotional nuance, exact pitch contour,
        character identity, detailed prosody, voice texture.
        """
        rate: Optional[int] = None
        volume: Optional[int] = None
        warnings = [
            "Windows System TTS cannot reproduce the target character timbre "
            "or full expressive profile.",
            "Output is NOT a cloned or synthesized character voice.",
            "Label: Beta default system voice — styled with available Windows hints.",
        ]

        if self.style.speaking_rate:
            _rate_map = {
                "very slow": -5, "slow": -3, "normal": 0,
                "fast": 3, "very fast": 5,
            }
            rate = _rate_map.get(self.style.speaking_rate.lower())
            if rate is None:
                warnings.append(
                    f"speaking_rate value '{self.style.speaking_rate}' "
                    "could not be mapped to Windows SAPI Rate; using default."
                )

        if self.style.energy:
            _energy_map = {
                "whispered": 40, "calm": 60, "moderate": 80,
                "high energy": 100, "very high energy": 100,
            }
            volume = _energy_map.get(self.style.energy.lower())
            if volume is None:
                warnings.append(
                    f"energy value '{self.style.energy}' could not be mapped "
                    "to Windows volume; using default."
                )

        # Timbre, emotional nuance, pitch contour — not mappable to Windows TTS
        if self.style.timbre_descriptors:
            warnings.append(
                "Timbre descriptors are NOT supported by Windows System TTS: "
                + ", ".join(self.style.timbre_descriptors)
            )
        if self.style.emotional_tone:
            warnings.append(
                f"emotional_tone '{self.style.emotional_tone}' is NOT "
                "reproducible by Windows System TTS."
            )

        return {
            "rate": rate,
            "volume": volume,
            "voice_name_hint": None,  # no character-specific SAPI voice available
            "warnings": warnings,
            "unsupported_hints": [
                "timbre_descriptors",
                "pitch_tendency",
                "rhythm",
                "pause_style",
                "expressiveness",
                "emotional_tone",
                "conversational_attitude",
                "pronunciation_notes",
                "character_identity",
            ],
        }
