"""
tests/integration/speech/test_windows_tts.py

Integration tests for WindowsSystemTtsProvider.

These tests call real Windows TTS — they require a Windows machine with
at least one SAPI voice installed.

Marks:
  - All tests are marked `windows_tts` so they can be run selectively.
  - Playback tests are marked `manual` — do not run in CI automatically.

Run synthesis only:
  pytest tests/integration/speech/ -m "windows_tts and not manual"

Run with playback (manual, requires speakers):
  pytest tests/integration/speech/ -m "windows_tts"
"""

from __future__ import annotations

import pytest
from pathlib import Path

# ---------------------------------------------------------------------------
# Availability guard — skip entire module if not on Windows
# ---------------------------------------------------------------------------
import platform

pytestmark = pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Windows TTS integration tests require a Windows machine.",
)

from beta.infrastructure.speech.tts.windows_system import WindowsSystemTtsProvider
from beta.interaction.voice.contracts import SpeechRequest

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_OUTPUT_DIR = _PROJECT_ROOT / "var" / "artifacts" / "audio"


@pytest.fixture(scope="module")
def provider():
    return WindowsSystemTtsProvider(output_dir=_OUTPUT_DIR)


@pytest.mark.windows_tts
class TestListVoices:
    def test_list_voices_returns_list(self, provider):
        voices = provider.list_voices()
        # May be empty on systems without voices — that is also valid here.
        assert isinstance(voices, list)

    def test_voice_has_name(self, provider):
        voices = provider.list_voices()
        if not voices:
            pytest.skip("No SAPI voices installed on this machine.")
        for v in voices:
            assert v.name, "Voice name must not be empty"


@pytest.mark.windows_tts
class TestSynthesis:
    def test_synthesize_short_text(self, provider, tmp_path):
        out = tmp_path / "var" / "artifacts" / "audio" / "test_short.wav"
        out.parent.mkdir(parents=True)
        req = SpeechRequest(
            text="Hello.",
            play_audio=False,
            output_path=out,
        )
        artifact = provider.synthesize(req)
        assert artifact.path.exists()
        assert artifact.size_bytes > 0
        assert artifact.format == "wav"
        assert artifact.provider == "windows-system"

    def test_output_is_inside_var(self, provider, tmp_path):
        out = tmp_path / "var" / "artifacts" / "audio" / "test_var_check.wav"
        out.parent.mkdir(parents=True)
        req = SpeechRequest(
            text="Test path.",
            play_audio=False,
            output_path=out,
        )
        artifact = provider.synthesize(req)
        path_str = str(artifact.path).replace("\\", "/").lower()
        assert "var" in path_str, f"Expected path inside var/, got: {artifact.path}"

    def test_unicode_vietnamese_text(self, provider, tmp_path):
        out = tmp_path / "var" / "artifacts" / "audio" / "test_vi.wav"
        out.parent.mkdir(parents=True)
        req = SpeechRequest(
            text="Xin chào, tôi là Beta. Bầu trời hôm nay rất đẹp.",
            language="vi-VN",
            play_audio=False,
            output_path=out,
        )
        artifact = provider.synthesize(req)
        assert artifact.path.exists()
        assert artifact.size_bytes > 0

    def test_no_overwrite_existing_file(self, provider, tmp_path):
        out = tmp_path / "var" / "artifacts" / "audio" / "test_overwrite.wav"
        out.parent.mkdir(parents=True)
        out.write_bytes(b"existing content")

        from beta.interaction.voice.errors import AudioOutputError
        req = SpeechRequest(
            text="Should not overwrite.",
            play_audio=False,
            output_path=out,
        )
        with pytest.raises(AudioOutputError, match="already exists"):
            provider.synthesize(req)

    def test_auto_path_is_under_artifacts(self, provider):
        req = SpeechRequest(
            text="Auto path test.",
            play_audio=False,
        )
        artifact = provider.synthesize(req)
        assert artifact.path.exists()
        path_str = str(artifact.path).replace("\\", "/").lower()
        assert "var" in path_str
        # Cleanup
        artifact.path.unlink(missing_ok=True)


@pytest.mark.windows_tts
@pytest.mark.manual
class TestPlayback:
    """
    Manual tests — require speakers.
    Run with: pytest -m "windows_tts and manual"
    NOT run in automated CI.
    """

    def test_playback_audible(self, provider, tmp_path):
        out = tmp_path / "var" / "artifacts" / "audio" / "test_playback.wav"
        out.parent.mkdir(parents=True)
        req = SpeechRequest(
            text="Playback test. Bạn có nghe thấy tôi không?",
            play_audio=False,
            output_path=out,
        )
        artifact = provider.synthesize(req)
        assert artifact.path.exists()

        from beta.infrastructure.speech.playback.windows import WindowsAudioPlayer
        player = WindowsAudioPlayer()
        result = player.play(artifact.path)
        assert result is True
