import os
from pathlib import Path

import pytest
from beta.infrastructure.speech.tts.windows_system import WindowsSystemTtsProvider
from beta.interaction.voice.contracts import VoiceHint

# Integration test - only run on Windows
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows TTS only works on Windows")


def test_windows_system_tts_generate_wav(tmp_path: Path):
    provider = WindowsSystemTtsProvider()
    output_path = tmp_path / "output.wav"
    
    # Use a small rate and volume hint
    hint = VoiceHint(speaking_rate=1.5, volume=0.5)
    
    artifact = provider.synthesize("Chào bạn, tôi là hệ thống tự động.", hint, output_path)
    
    assert artifact.path.exists()
    assert artifact.path.stat().st_size > 1000  # Should be a valid wav file
    assert artifact.format == "wav"
    assert artifact.provider == "windows-system"
