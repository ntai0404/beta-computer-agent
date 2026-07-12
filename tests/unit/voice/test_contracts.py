"""
tests/unit/voice/test_contracts.py

Unit tests for SpeechRequest validation.

No provider calls. No audio files. No sound output.
"""

import pytest
from pathlib import Path

from beta.interaction.voice.contracts import (
    RATE_MAX,
    RATE_MIN,
    VOLUME_MAX,
    VOLUME_MIN,
    SpeechRequest,
)


class TestSpeechRequestValidation:
    def test_empty_text_is_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            SpeechRequest(text="")

    def test_whitespace_only_text_is_rejected(self):
        with pytest.raises(ValueError, match="must not be empty"):
            SpeechRequest(text="   ")

    def test_valid_text_is_accepted(self):
        req = SpeechRequest(text="Xin chào")
        assert req.text == "Xin chào"

    def test_rate_below_min_is_rejected(self):
        with pytest.raises(ValueError, match="rate"):
            SpeechRequest(text="hello", rate=RATE_MIN - 1)

    def test_rate_above_max_is_rejected(self):
        with pytest.raises(ValueError, match="rate"):
            SpeechRequest(text="hello", rate=RATE_MAX + 1)

    def test_rate_at_boundaries_is_accepted(self):
        SpeechRequest(text="hello", rate=RATE_MIN)
        SpeechRequest(text="hello", rate=RATE_MAX)

    def test_volume_below_zero_is_rejected(self):
        with pytest.raises(ValueError, match="volume"):
            SpeechRequest(text="hello", volume=-1)

    def test_volume_above_100_is_rejected(self):
        with pytest.raises(ValueError, match="volume"):
            SpeechRequest(text="hello", volume=101)

    def test_volume_at_boundaries_is_accepted(self):
        SpeechRequest(text="hello", volume=VOLUME_MIN)
        SpeechRequest(text="hello", volume=VOLUME_MAX)

    def test_output_path_inside_src_is_rejected(self, tmp_path):
        bad_path = tmp_path / "src" / "audio.wav"
        with pytest.raises(ValueError, match="src"):
            SpeechRequest(text="hello", output_path=bad_path)

    def test_output_path_outside_var_is_rejected(self, tmp_path):
        bad_path = tmp_path / "audio.wav"
        with pytest.raises(ValueError, match="var"):
            SpeechRequest(text="hello", output_path=bad_path)

    def test_output_path_inside_var_is_accepted(self, tmp_path):
        # Simulate a path inside a "var" subtree
        var_dir = tmp_path / "var" / "artifacts" / "audio"
        var_dir.mkdir(parents=True)
        ok_path = var_dir / "test.wav"
        # Should not raise
        req = SpeechRequest(text="hello", output_path=ok_path)
        assert req.output_path is not None

    def test_no_output_path_is_valid(self):
        req = SpeechRequest(text="hello", output_path=None)
        assert req.output_path is None

    def test_play_audio_default_is_true(self):
        req = SpeechRequest(text="hello")
        assert req.play_audio is True

    def test_play_audio_can_be_disabled(self):
        req = SpeechRequest(text="hello", play_audio=False)
        assert req.play_audio is False
