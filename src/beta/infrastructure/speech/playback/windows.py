"""
infrastructure/speech/playback/windows.py

Audio playback adapter for Windows using PowerShell + System.Media.SoundPlayer.

Responsibilities:
  - Play a WAV file that already exists on disk.
  - Wait for playback to finish (blocking).
  - Return success status.

Does NOT synthesize audio. Synthesis is TtsProvider's job.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Optional

from beta.interaction.voice.errors import PlaybackError

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS: int = 120

# PowerShell script: plays a WAV file synchronously and exits.
# The WAV path is passed as an argument — never interpolated into the script body.
_PLAY_SCRIPT = r"""
param([string]$WavPath)
$ErrorActionPreference = 'Stop'

if (-not (Test-Path $WavPath)) {
    throw "Audio file not found: $WavPath"
}

Add-Type -AssemblyName System.Windows.Forms
$player = New-Object System.Media.SoundPlayer($WavPath)
try {
    $player.PlaySync()
} finally {
    $player.Dispose()
}
"""


class WindowsAudioPlayer:
    """
    Plays WAV files synchronously using Windows System.Media.SoundPlayer.

    Does not synthesize audio. Only plays files that already exist.
    """

    def __init__(self, timeout: int = _DEFAULT_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout

    def play(self, wav_path: Path) -> bool:
        """
        Play a WAV file and block until playback is complete.

        Args:
            wav_path: Absolute path to an existing WAV file.

        Returns:
            True on success.

        Raises:
            PlaybackError: if the file does not exist, is invalid, or playback fails.
        """
        if not wav_path.exists():
            raise PlaybackError(f"Audio file not found: {wav_path}")

        if wav_path.stat().st_size == 0:
            raise PlaybackError(f"Audio file is empty: {wav_path}")

        script_file: Optional[Path] = None
        try:
            script_file = _write_temp_ps1(_PLAY_SCRIPT)
            cmd = [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy", "Bypass",
                "-File", str(script_file),
                str(wav_path),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self._timeout,
                shell=False,
            )
            if result.returncode != 0:
                raise PlaybackError(
                    f"Audio playback failed (exit {result.returncode}).\n"
                    f"stderr: {result.stderr.strip()}"
                )
            logger.info("Played %s", wav_path)
            return True

        except subprocess.TimeoutExpired as exc:
            raise PlaybackError(
                f"Audio playback timed out after {self._timeout}s: {wav_path}"
            ) from exc
        except PlaybackError:
            raise
        except Exception as exc:
            raise PlaybackError(f"Unexpected playback error: {exc}") from exc
        finally:
            _cleanup(script_file)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_temp_ps1(script: str) -> Path:
    fd, name = tempfile.mkstemp(suffix=".ps1", prefix="beta_play_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(script)
    except Exception:
        os.unlink(name)
        raise
    return Path(name)


def _cleanup(path: Optional[Path]) -> None:
    if path and path.exists():
        try:
            path.unlink()
        except OSError as exc:
            logger.warning("Failed to clean up temp file %s: %s", path, exc)
