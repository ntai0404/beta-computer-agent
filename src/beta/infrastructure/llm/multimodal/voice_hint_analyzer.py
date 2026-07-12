"""
infrastructure/llm/multimodal/voice_hint_analyzer.py

VoiceHintAnalyzer orchestrates multimodal voice analysis.

It:
  - validates the reference file locally;
  - checks provider capabilities before sending any media;
  - builds the analysis prompt with correct constraints;
  - calls the provider;
  - post-processes the result into a VoiceHint;
  - never produces fake results when the provider is unavailable.

Rules enforced in the prompt (see ANALYSIS_PROMPT_TEMPLATE):
  - do not identify the speaker;
  - do not name the character;
  - only analyze acoustic/stylistic features;
  - distinguish observed / inferred / unknown;
  - return structured JSON;
  - report confidence;
  - warn about quality issues.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

from beta.infrastructure.llm.multimodal.base import (
    AnalysisRequest,
    AnalysisResult,
    MultimodalVoiceAnalyzer,
)
from beta.infrastructure.llm.multimodal.voice_hint_contracts import (
    AudioQualityAssessment,
    SourceReference,
    VoiceHint,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Analysis Prompt Template
# ---------------------------------------------------------------------------

ANALYSIS_PROMPT_TEMPLATE = """
You are a voice and speech analysis assistant. Your task is to analyze the
provided audio or video reference and produce a structured description of
speaking style and audio quality.

RULES YOU MUST FOLLOW:
1. Do NOT attempt to identify, name, or guess the identity of the speaker.
2. Do NOT name the character or any person.
3. Only analyze acoustic features and speaking style that you can observe.
4. For every field, indicate whether the value is:
   - "directly_observed" (clearly audible in the reference),
   - "inferred" (reasonable conclusion from the audio), or
   - "unknown" (cannot be determined from this reference).
5. Return a structured JSON object. Do not include prose paragraphs.
6. State your confidence level: "high", "medium", "low", or "insufficient_data".
7. Warn about any of the following if present:
   - clip is too short (under 5 seconds of clean speech);
   - background music is present;
   - multiple speakers are audible;
   - sound effects overlay the voice;
   - heavy audio compression is detectable;
   - transcript is uncertain;
   - audio quality is insufficient for voice model training or cloning.
8. Do NOT describe how to "exactly imitate" a real person.
9. Do NOT return private reasoning, chain-of-thought, or scratchpad text.
10. Keep the style_prompt field to one or two sentences maximum.

CONTEXT (provided by the caller, do not use to identify the speaker):
- Profile alias: {persona_alias}
- Language hint: {language_hint}
- Scene/category: {scene_context}
- Pre-existing transcript (if any): {transcript}

OUTPUT FORMAT (JSON, no other text):
{{
  "speaking_rate": "slow | normal | fast | very fast | unknown",
  "speaking_rate_status": "directly_observed | inferred | unknown",
  "pitch_tendency": "high | mid-high | mid | low | unknown",
  "pitch_tendency_status": "directly_observed | inferred | unknown",
  "energy": "whispered | calm | moderate | high energy | very high energy | unknown",
  "energy_status": "directly_observed | inferred | unknown",
  "rhythm": "description or unknown",
  "rhythm_status": "directly_observed | inferred | unknown",
  "pause_style": "description or unknown",
  "pause_style_status": "directly_observed | inferred | unknown",
  "expressiveness": "highly expressive | moderate | flat | theatrical | unknown",
  "emotional_tone": "description or unknown",
  "conversational_attitude": "description or unknown",
  "timbre_descriptors": ["descriptor1", "descriptor2"],
  "pronunciation_notes": "description or null",
  "language": "BCP-47 tag or null",
  "style_prompt": "One or two sentence description of speaking style. No speaker name.",
  "audio_quality": {{
    "background_noise": "directly_observed | inferred | unknown",
    "background_music": "directly_observed | inferred | unknown",
    "multiple_speakers": "directly_observed | inferred | unknown",
    "sound_effects": "directly_observed | inferred | unknown",
    "compression_artifacts": "directly_observed | inferred | unknown",
    "sufficient_for_cloning": true | false,
    "sufficient_for_analysis": true | false,
    "warnings": ["list of specific quality warnings"]
  }},
  "transcript": "verbatim transcript or null",
  "transcript_confidence": "high | medium | low | insufficient_data",
  "overall_confidence": "high | medium | low | insufficient_data",
  "warnings": ["list of analysis-level warnings"]
}}
""".strip()


# ---------------------------------------------------------------------------
# VoiceHintAnalyzer
# ---------------------------------------------------------------------------


class VoiceHintAnalyzer:
    """
    Orchestrates multimodal voice reference analysis.

    Takes a local audio/video file and a MultimodalVoiceAnalyzer implementation,
    produces a populated VoiceHint.

    Does not call any provider if the reference file does not exist.
    Does not produce fake results if the provider is unavailable or unconfigured.
    """

    def __init__(self, provider: MultimodalVoiceAnalyzer) -> None:
        self._provider = provider

    def analyze(
        self,
        reference_path: Path,
        character_profile_id: str,
        persona_alias: str,
        existing_transcript: Optional[str] = None,
        language_hint: Optional[str] = None,
        scene_context: Optional[str] = None,
        dry_run: bool = False,
    ) -> VoiceHint:
        """
        Analyze a voice reference and return a VoiceHint.

        Args:
            reference_path: Local path to the audio or video file.
            character_profile_id: Profile ID (e.g. 'mambo').
            persona_alias: Display alias (e.g. 'Mambo').
            existing_transcript: Pre-existing transcript if available.
            language_hint: BCP-47 language of the reference.
            scene_context: Optional scene or category label from the source.
            dry_run: If True, validate inputs but do not call the provider.

        Returns:
            A VoiceHint. If dry_run=True or provider unavailable, returns
            a pending VoiceHint with appropriate warnings.

        Raises:
            FileNotFoundError: if reference_path does not exist.
            ValueError: if reference_path is not a supported media file.
        """
        # --- Validate reference file
        if not reference_path.exists():
            raise FileNotFoundError(
                f"Voice reference not found: {reference_path}"
            )

        media_type = _detect_media_type(reference_path)
        if media_type is None:
            raise ValueError(
                f"Unsupported media type for: {reference_path}. "
                "Supported: .wav, .mp3, .ogg, .flac, .mp4, .webm, .mkv"
            )

        file_hash = _sha256(reference_path)
        source_ref = SourceReference(
            path=str(reference_path),
            sha256=file_hash,
            media_type=media_type,
        )

        # --- Base VoiceHint (always unresolved canonical identity)
        hint = VoiceHint(
            profile_id=character_profile_id,
            persona_alias=persona_alias,
            canonical_identity_status="unresolved",
            source_references=[source_ref],
        )

        if dry_run:
            hint.warnings.append(
                "dry_run=True: provider was not called. "
                "Validation passed; reference file exists and hash computed."
            )
            logger.info("VoiceHintAnalyzer dry_run: %s", reference_path)
            return hint

        # --- Check provider health (no fake results on failure)
        try:
            self._provider.health_check()
        except Exception as exc:
            hint.warnings.append(
                f"Multimodal provider '{self._provider.provider_id}' is not available: {exc}. "
                "Voice Hint is pending analysis. No fake result generated."
            )
            logger.warning(
                "VoiceHintAnalyzer: provider not available: %s", exc
            )
            return hint

        # --- Check capabilities before sending media
        caps = self._provider.capabilities()
        request = AnalysisRequest(
            reference_path=reference_path,
            character_profile_id=character_profile_id,
            persona_alias=persona_alias,
            existing_transcript=existing_transcript,
            language_hint=language_hint,
            additional_context=scene_context,
        )

        fallbacks: list[str] = []
        if media_type.startswith("audio/") and not caps.supports_audio_input:
            hint.warnings.append(
                f"Provider '{self._provider.provider_id}' does not support "
                "direct audio input. "
                "Falling back to transcript-only analysis (if transcript provided). "
                "Audio timbre and prosody details will be unavailable."
            )
            if existing_transcript is None:
                hint.warnings.append(
                    "No transcript provided and audio input is unsupported. "
                    "Voice Hint is pending analysis."
                )
                return hint
            fallbacks.append("transcript_only")

        if media_type.startswith("video/") and not caps.supports_video_input:
            hint.warnings.append(
                f"Provider '{self._provider.provider_id}' does not support "
                "video input. Falling back to transcript-only analysis."
            )
            fallbacks.append("transcript_only")

        # --- Call provider
        try:
            if media_type.startswith("audio/") and caps.supports_audio_input:
                result = self._provider.analyze_audio(request)
            elif media_type.startswith("video/") and caps.supports_video_input:
                result = self._provider.analyze_video(request)
            else:
                # Transcript-only fallback was validated above
                result = self._provider.analyze_audio(request)

            populated = result.voice_hint
            populated.warnings.extend(hint.warnings)
            for fb in (result.fallbacks_used + fallbacks):
                if fb not in populated.warnings:
                    populated.warnings.append(f"Fallback used: {fb}")
            return populated

        except Exception as exc:
            hint.warnings.append(
                f"Analysis failed: {exc}. Voice Hint is pending."
            )
            logger.error("VoiceHintAnalyzer analysis error: %s", exc)
            return hint


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def build_analysis_prompt(
    persona_alias: str,
    language_hint: Optional[str] = None,
    scene_context: Optional[str] = None,
    transcript: Optional[str] = None,
) -> str:
    """Build the structured analysis prompt for the multimodal provider."""
    return ANALYSIS_PROMPT_TEMPLATE.format(
        persona_alias=persona_alias,
        language_hint=language_hint or "unknown",
        scene_context=scene_context or "not specified",
        transcript=transcript or "none",
    )


def _detect_media_type(path: Path) -> Optional[str]:
    """Return a MIME-like type string based on file extension, or None."""
    ext = path.suffix.lower()
    _map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".flac": "audio/flac",
        ".m4a": "audio/mp4",
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/x-matroska",
        ".avi": "video/avi",
    }
    return _map.get(ext)


def _sha256(path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
