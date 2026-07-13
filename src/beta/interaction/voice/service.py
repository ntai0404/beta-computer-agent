"""
interaction/voice/service.py

Voice Service Orchestrator.
Orchestrates profile resolution, synthesis, conversion, and playback.
"""

from __future__ import annotations

import logging
from pathlib import Path

from beta.interaction.voice.contracts import (
    AudioPlayer,
    PipelinePreference,
    SpeechRequest,
    TtsProvider,
    VoiceConversionProvider,
    VoicePipelineResult,
)
from beta.interaction.voice.resolver import VoiceProfileResolver
from beta.interaction.voice.pipeline import VoicePipelineSelector

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(
        self,
        resolver: VoiceProfileResolver,
        pipeline_selector: VoicePipelineSelector,
        tts_providers: dict[str, TtsProvider],
        conversion_providers: dict[str, VoiceConversionProvider],
        audio_player: AudioPlayer,
        artifacts_dir: Path
    ):
        self.resolver = resolver
        self.pipeline_selector = pipeline_selector
        self.tts_providers = tts_providers
        self.conversion_providers = conversion_providers
        self.audio_player = audio_player
        self.artifacts_dir = artifacts_dir
        
        self.audio_dir = artifacts_dir / "audio"
        self.audio_dir.mkdir(parents=True, exist_ok=True)

    def speak(self, request: SpeechRequest) -> VoicePipelineResult:
        """
        Executes the speech pipeline.
        """
        trace = []
        warnings = []
        
        trace.append(f"Request: {request.text[:50]}...")
        
        # 1. Resolve profile
        profile = self.resolver.resolve(request.character_profile_id)
        trace.append(f"Profile resolved: {profile.persona_alias} (Status: {profile.readiness_status.value})")
        warnings.extend(profile.warnings)
        
        # 2. Select pipeline
        self.pipeline_selector.select(profile, request.pipeline_preference)
        trace.append(f"Pipeline selected: {profile.selected_pipeline.value}")
        
        if profile.selected_pipeline == PipelinePreference.SYSTEM_TTS:
            logger.warning(f"Using Windows system voice for profile '{profile.persona_alias}'. This is not a cloned or character-matched voice.")
            warnings.append(f"Using Windows system voice for profile '{profile.persona_alias}'. This is not a cloned or character-matched voice.")
            
        # 3. Generate Audio
        intermediate_artifacts = []
        final_artifact = None
        
        tts_provider = self.tts_providers.get(profile.selected_tts_provider)
        if not tts_provider:
            raise ValueError(f"TTS Provider not found: {profile.selected_tts_provider}")
            
        # Modify hint based on request overrides
        hint = profile.voice_hint
        if hint:
            hint.speaking_rate = request.rate
            hint.volume = request.volume
            
        # Determine output path for TTS
        # If there's conversion later, TTS is intermediate
        is_final = profile.selected_conversion_provider is None
        out_name = f"tts_{profile.character_profile_id}_{hash(request.text)}.wav"
        
        if is_final:
            tts_out = request.output_path or (self.audio_dir / "final" / out_name)
        else:
            tts_out = self.audio_dir / "intermediate" / out_name
            
        tts_out.parent.mkdir(parents=True, exist_ok=True)
        
        trace.append(f"Running TTS: {tts_provider.provider_id}")
        tts_artifact = tts_provider.synthesize(request.text, hint, tts_out)
        tts_artifact.character_profile_id = profile.character_profile_id
        
        if is_final:
            final_artifact = tts_artifact
        else:
            intermediate_artifacts.append(tts_artifact)
            
            # 4. Conversion
            conv_provider = self.conversion_providers.get(profile.selected_conversion_provider)
            if not conv_provider:
                raise ValueError(f"Conversion Provider not found: {profile.selected_conversion_provider}")
                
            trace.append(f"Running Conversion: {conv_provider.provider_id}")
            conv_out = request.output_path or (self.audio_dir / "final" / f"conv_{profile.character_profile_id}_{hash(request.text)}.wav")
            conv_out.parent.mkdir(parents=True, exist_ok=True)
            
            # This will raise an error currently since models are blocked.
            final_artifact = conv_provider.convert(tts_artifact.path, profile, conv_out)
            final_artifact.character_profile_id = profile.character_profile_id
            
        # 5. Playback
        played = False
        if request.play_audio and final_artifact:
            trace.append("Playing audio")
            played = self.audio_player.play(final_artifact.path)
            
        trace.append("Pipeline complete")
        
        return VoicePipelineResult(
            request=request,
            resolved_profile=profile,
            intermediate_artifacts=intermediate_artifacts,
            final_artifact=final_artifact,
            played=played,
            warnings=warnings,
            pipeline_trace=trace
        )
