"""
interaction/voice/pipeline.py

Pipeline selector for Voice Engine.
"""

from __future__ import annotations

import logging

from beta.interaction.voice.contracts import PipelinePreference, ReadinessStatus, ResolvedVoiceProfile

logger = logging.getLogger(__name__)


class VoicePipelineSelector:
    def select(self, profile: ResolvedVoiceProfile, preference: PipelinePreference) -> None:
        """
        Updates the profile with the selected pipeline in-place.
        Currently falls back to SYSTEM_TTS if models are untrusted/blocked.
        """
        
        # If user explicitly wants a pipeline, we check if it's possible.
        if preference == PipelinePreference.SYSTEM_TTS:
            profile.selected_pipeline = PipelinePreference.SYSTEM_TTS
            profile.selected_tts_provider = "windows-system"
            profile.selected_conversion_provider = None
            return

        if profile.readiness_status in (ReadinessStatus.BLOCKED, ReadinessStatus.FALLBACK_READY, ReadinessStatus.UNRESOLVED):
            profile.selected_pipeline = PipelinePreference.SYSTEM_TTS
            profile.selected_tts_provider = "windows-system"
            profile.selected_conversion_provider = None
            
            if profile.readiness_status == ReadinessStatus.BLOCKED:
                profile.warnings.append("Requested auto/advanced pipeline, but models are blocked/untrusted. Forced fallback to SYSTEM_TTS.")
            return

        # Future states (trusted models)
        if profile.readiness_status == ReadinessStatus.CONVERSION_READY:
            profile.selected_pipeline = PipelinePreference.BASE_TTS_PLUS_CONVERSION
            profile.selected_tts_provider = "windows-system"  # Or F5, etc.
            profile.selected_conversion_provider = "rvc"
            return
            
        # Default fallback
        profile.selected_pipeline = PipelinePreference.SYSTEM_TTS
        profile.selected_tts_provider = "windows-system"
        profile.selected_conversion_provider = None
