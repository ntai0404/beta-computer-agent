"""
tests/unit/voice/test_voice_service.py

Unit tests for VoiceService orchestration.

Provider and player are mocked — no real synthesis or audio output.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, call

from beta.interaction.voice.contracts import (
    SpeechArtifact,
    SpeechRequest,
    SpeechResult,
)
from beta.interaction.voice.errors import TtsProviderError
from beta.interaction.voice.service import VoiceService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _fake_artifact(path: Path) -> SpeechArtifact:
    return SpeechArtifact(
        path=path,
        format="wav",
        provider="mock",
        voice_name="MockVoice",
        size_bytes=1024,
        created_at=datetime.now(timezone.utc),
        metadata={},
    )


@pytest.fixture
def wav_path(tmp_path):
    p = tmp_path / "var" / "artifacts" / "audio" / "test.wav"
    p.parent.mkdir(parents=True)
    p.write_bytes(b"RIFF" + b"\x00" * 100)  # dummy bytes, not real WAV
    return p


@pytest.fixture
def mock_provider(wav_path):
    provider = MagicMock()
    provider.provider_id = "mock"
    provider.synthesize.return_value = _fake_artifact(wav_path)
    provider.list_voices.return_value = []
    return provider


@pytest.fixture
def mock_player():
    player = MagicMock()
    player.play.return_value = True
    return player


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestVoiceService:
    def test_speak_calls_provider(self, mock_provider, mock_player, wav_path):
        svc = VoiceService(tts_provider=mock_provider, audio_player=mock_player)
        req = SpeechRequest(text="hello", play_audio=True, output_path=wav_path)
        svc.speak(req)
        mock_provider.synthesize.assert_called_once_with(req)

    def test_speak_calls_player_when_play_audio_true(
        self, mock_provider, mock_player, wav_path
    ):
        svc = VoiceService(tts_provider=mock_provider, audio_player=mock_player)
        req = SpeechRequest(text="hello", play_audio=True, output_path=wav_path)
        svc.speak(req)
        mock_player.play.assert_called_once_with(wav_path)

    def test_speak_does_not_call_player_when_play_audio_false(
        self, mock_provider, mock_player, wav_path
    ):
        svc = VoiceService(tts_provider=mock_provider, audio_player=mock_player)
        req = SpeechRequest(text="hello", play_audio=False, output_path=wav_path)
        result = svc.speak(req)
        mock_player.play.assert_not_called()
        assert result.played is False

    def test_speak_without_player_does_not_raise(self, mock_provider, wav_path):
        svc = VoiceService(tts_provider=mock_provider, audio_player=None)
        req = SpeechRequest(text="hello", play_audio=True, output_path=wav_path)
        result = svc.speak(req)
        assert result.played is False
        assert any("no audio player" in w.lower() for w in result.warnings)

    def test_provider_error_is_propagated(self, mock_provider, mock_player, wav_path):
        mock_provider.synthesize.side_effect = TtsProviderError("synth failed")
        svc = VoiceService(tts_provider=mock_provider, audio_player=mock_player)
        req = SpeechRequest(text="hello", play_audio=True, output_path=wav_path)
        with pytest.raises(TtsProviderError, match="synth failed"):
            svc.speak(req)

    def test_playback_failure_adds_warning_not_exception(
        self, mock_provider, mock_player, wav_path
    ):
        mock_player.play.side_effect = Exception("speaker broken")
        svc = VoiceService(tts_provider=mock_provider, audio_player=mock_player)
        req = SpeechRequest(text="hello", play_audio=True, output_path=wav_path)
        result = svc.speak(req)
        assert result.played is False
        assert any("Playback failed" in w for w in result.warnings)

    def test_result_contains_artifact(self, mock_provider, mock_player, wav_path):
        svc = VoiceService(tts_provider=mock_provider, audio_player=mock_player)
        req = SpeechRequest(text="hello", play_audio=False, output_path=wav_path)
        result = svc.speak(req)
        assert isinstance(result, SpeechResult)
        assert result.artifact.provider == "mock"

    def test_synthesis_happens_before_playback(
        self, mock_provider, mock_player, wav_path
    ):
        """Verify synthesis is called before play (ordering via side effects)."""
        call_order = []
        mock_provider.synthesize.side_effect = (
            lambda r: call_order.append("synth") or _fake_artifact(wav_path)
        )
        mock_player.play.side_effect = (
            lambda p: call_order.append("play") or True
        )
        svc = VoiceService(tts_provider=mock_provider, audio_player=mock_player)
        req = SpeechRequest(text="hello", play_audio=True, output_path=wav_path)
        svc.speak(req)
        assert call_order == ["synth", "play"]

    def test_list_voices_delegates_to_provider(self, mock_provider):
        svc = VoiceService(tts_provider=mock_provider)
        svc.list_voices()
        mock_provider.list_voices.assert_called_once()
