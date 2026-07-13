import pytest
from beta.interaction.voice.contracts import PipelinePreference, ReadinessStatus, ResolvedVoiceProfile, VoiceHint
from beta.interaction.voice.pipeline import VoicePipelineSelector


def create_dummy_profile(readiness: ReadinessStatus) -> ResolvedVoiceProfile:
    return ResolvedVoiceProfile(
        profile_id="test",
        character_profile_id="test",
        persona_alias="Test",
        canonical_identity_status="unresolved",
        selected_pipeline=PipelinePreference.AUTO,
        selected_tts_provider="none",
        selected_conversion_provider=None,
        selected_voice_name=None,
        voice_hint=VoiceHint(),
        model_paths={},
        provenance={},
        warnings=[],
        readiness_status=readiness
    )


def test_selector_fallback_ready():
    profile = create_dummy_profile(ReadinessStatus.FALLBACK_READY)
    selector = VoicePipelineSelector()
    
    selector.select(profile, PipelinePreference.AUTO)
    assert profile.selected_pipeline == PipelinePreference.SYSTEM_TTS
    assert profile.selected_tts_provider == "windows-system"


def test_selector_blocked_forces_fallback():
    profile = create_dummy_profile(ReadinessStatus.BLOCKED)
    selector = VoicePipelineSelector()
    
    selector.select(profile, PipelinePreference.AUTO)
    assert profile.selected_pipeline == PipelinePreference.SYSTEM_TTS
    assert profile.selected_tts_provider == "windows-system"
    assert "Forced fallback" in profile.warnings[0]


def test_selector_conversion_ready():
    profile = create_dummy_profile(ReadinessStatus.CONVERSION_READY)
    selector = VoicePipelineSelector()
    
    selector.select(profile, PipelinePreference.AUTO)
    assert profile.selected_pipeline == PipelinePreference.BASE_TTS_PLUS_CONVERSION
    assert profile.selected_tts_provider == "windows-system"
    assert profile.selected_conversion_provider == "rvc"


def test_selector_explicit_system_tts():
    profile = create_dummy_profile(ReadinessStatus.CONVERSION_READY)
    selector = VoicePipelineSelector()
    
    selector.select(profile, PipelinePreference.SYSTEM_TTS)
    assert profile.selected_pipeline == PipelinePreference.SYSTEM_TTS
    assert profile.selected_tts_provider == "windows-system"
    assert profile.selected_conversion_provider is None
