from pathlib import Path

from beta.infrastructure.llm.multimodal.base import (
    AnalysisCapabilities,
    AnalysisRequest,
    AnalysisResult,
    MultimodalVoiceAnalyzer,
)
from beta.infrastructure.llm.multimodal.voice_hint_analyzer import VoiceHintAnalyzer
from beta.infrastructure.llm.multimodal.voice_hint_contracts import VoiceHint


class NoAudioProvider(MultimodalVoiceAnalyzer):
    @property
    def provider_id(self) -> str:
        return "no-audio"

    def capabilities(self) -> AnalysisCapabilities:
        return AnalysisCapabilities(
            supports_audio_input=False,
            supports_video_input=False,
            supports_image_input=False,
            supports_transcription=False,
            supports_structured_output=True,
        )

    def analyze_audio(self, request: AnalysisRequest) -> AnalysisResult:
        raise AssertionError("audio should not be sent when unsupported")

    def analyze_video(self, request: AnalysisRequest) -> AnalysisResult:
        raise AssertionError("video should not be sent when unsupported")

    def transcribe(self, request: AnalysisRequest) -> str | None:
        return None

    def health_check(self) -> None:
        return None

    def supported_media_types(self) -> list[str]:
        return ["text"]


def test_voice_hint_analyzer_does_not_fake_transcript(tmp_path: Path):
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"RIFF synthetic")

    hint = VoiceHintAnalyzer(NoAudioProvider()).analyze(
        reference_path=audio,
        character_profile_id="mambo",
        persona_alias="Mambo",
    )

    assert isinstance(hint, VoiceHint)
    assert hint.transcript is None
    assert hint.overall_confidence == "insufficient_data"
    assert any("No transcript provided" in warning for warning in hint.warnings)
