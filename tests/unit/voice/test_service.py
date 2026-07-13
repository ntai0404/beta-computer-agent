import json
from pathlib import Path

import pytest
from beta.interaction.voice.contracts import (
    AudioPlayer,
    PipelinePreference,
    SpeechArtifact,
    SpeechRequest,
    TtsProvider,
    VoiceConversionProvider,
    VoiceHint,
)
from beta.interaction.voice.pipeline import VoicePipelineSelector
from beta.interaction.voice.resolver import VoiceProfileResolver
from beta.interaction.voice.service import VoiceService


class MockTtsProvider(TtsProvider):
    @property
    def provider_id(self) -> str:
        return "mock-tts"

    def synthesize(self, text: str, hint: VoiceHint | None, output_path: Path) -> SpeechArtifact:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("audio")
        return SpeechArtifact(
            path=output_path, format="wav", sample_rate=16000, channels=1,
            provider="mock-tts", pipeline="system_tts", character_profile_id="",
            generated_at="", size_bytes=5, checksum="", provenance="", warnings=[]
        )


class MockAudioPlayer(AudioPlayer):
    def __init__(self):
        self.played_path = None

    def play(self, audio_path: Path) -> bool:
        self.played_path = audio_path
        return True


def test_voice_service_fallback(tmp_path: Path):
    project_root = tmp_path / "project"
    profiles_dir = project_root / "profiles" / "characters" / "mambo"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "CHARACTER.md").write_text("**Display Alias:** Mambo", encoding="utf-8")
    
    resolver = VoiceProfileResolver(project_root)
    selector = VoicePipelineSelector()
    tts = MockTtsProvider()
    player = MockAudioPlayer()
    
    service = VoiceService(
        resolver=resolver,
        pipeline_selector=selector,
        tts_providers={"windows-system": tts},
        conversion_providers={},
        audio_player=player,
        artifacts_dir=project_root / "var" / "artifacts"
    )
    
    req = SpeechRequest(
        text="Hello",
        character_profile_id="mambo",
        pipeline_preference=PipelinePreference.AUTO,
        play_audio=True
    )
    
    result = service.speak(req)
    
    assert result.played is True
    assert player.played_path is not None
    assert result.final_artifact.provider == "mock-tts"
    assert "Using Windows system voice for profile 'Mambo'" in result.warnings[0]
    assert len(result.intermediate_artifacts) == 0
