"""
interaction/voice/service.py

VoiceService — the single orchestration point for the voice interaction layer.

Responsibilities:
  - Validate SpeechRequest.
  - Call TtsProvider to produce a SpeechArtifact.
  - Optionally call AudioPlayer to play the result.
  - Return SpeechResult to the caller.

VoiceService knows nothing about:
  - PowerShell, Windows COM, or System.Speech.
  - WAV encoding or file writing.
  - MAS runtime, agents, or memory.
"""

from __future__ import annotations

import logging
from typing import Optional, Protocol, runtime_checkable

from beta.interaction.voice.contracts import SpeechRequest, SpeechResult
from beta.interaction.voice.errors import TtsProviderError, VoiceError
from beta.infrastructure.speech.audio.artifacts import wav_duration_ms
from beta.infrastructure.speech.tts.base import TtsProvider

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# AudioPlayer protocol — VoiceService depends on this, not a concrete class.
# ---------------------------------------------------------------------------


@runtime_checkable
class AudioPlayer(Protocol):
    """Minimal protocol for an audio playback adapter."""

    def play(self, wav_path) -> bool:
        """Play the given WAV file. Returns True on success."""
        ...


# ---------------------------------------------------------------------------
# VoiceService
# ---------------------------------------------------------------------------


class VoiceService:
    """
    Orchestrates the text → synthesis → playback pipeline.

    Dependencies are injected; this class does not instantiate providers.
    """

    def __init__(
        self,
        tts_provider: TtsProvider,
        audio_player: Optional[AudioPlayer] = None,
    ) -> None:
        """
        Args:
            tts_provider: A TtsProvider implementation.
            audio_player: Optional AudioPlayer; if None, playback is disabled
                          (equivalent to always play_audio=False).
        """
        self._tts = tts_provider
        self._player = audio_player

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def speak(self, request: SpeechRequest) -> SpeechResult:
        """
        Synthesize and optionally play speech.

        Args:
            request: Validated SpeechRequest (validation is in the dataclass).

        Returns:
            SpeechResult with artifact and playback status.

        Raises:
            VoiceError (or subclass) on failure.
        """
        logger.info(
            "VoiceService.speak: %d chars, profile=%s, play=%s",
            len(request.text),
            request.voice_profile_id,
            request.play_audio,
        )

        # 1. Synthesize
        try:
            artifact = self._tts.synthesize(request)
        except TtsProviderError:
            raise
        except Exception as exc:
            raise TtsProviderError(
                f"Unexpected error during synthesis: {exc}"
            ) from exc

        # 2. Measure duration (best-effort)
        duration_ms = wav_duration_ms(artifact.path)

        # 3. Playback
        played = False
        warnings = list(artifact.metadata.get("warnings", []))

        if request.play_audio and self._player is not None:
            try:
                played = self._player.play(artifact.path)
            except Exception as exc:
                # Playback failure is a warning, not a fatal error.
                # The artifact is still valid.
                warn = f"Playback failed (artifact retained): {exc}"
                warnings.append(warn)
                logger.warning(warn)
        elif request.play_audio and self._player is None:
            warnings.append(
                "play_audio=True but no audio player is configured."
            )

        return SpeechResult(
            request=request,
            artifact=artifact,
            played=played,
            duration_ms=duration_ms,
            warnings=warnings,
        )

    def list_voices(self):
        """Delegate to the TTS provider."""
        return self._tts.list_voices()

    def health_check(self) -> None:
        """Delegate to the TTS provider."""
        self._tts.health_check()
