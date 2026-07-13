"""
infrastructure/speech/playback/windows.py

Windows Audio Player using native winsound.
"""

from __future__ import annotations

import logging
import winsound
from pathlib import Path

from beta.interaction.voice.contracts import AudioPlayer

logger = logging.getLogger(__name__)


class WindowsAudioPlayer(AudioPlayer):
    def play(self, audio_path: Path) -> bool:
        """Plays the audio file using winsound."""
        if not audio_path.exists():
            logger.error(f"Cannot play audio, file not found: {audio_path}")
            return False
            
        try:
            logger.info(f"Playing audio: {audio_path}")
            winsound.PlaySound(str(audio_path), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            return True
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False
