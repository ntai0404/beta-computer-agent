"""
interaction/voice — public voice interaction interface.

Public exports:
  - SpeechRequest, SpeechArtifact, SpeechResult  (contracts)
  - VoiceError and subclasses                     (errors)

Note: VoiceService is NOT exported here to avoid circular imports with
infrastructure/speech/tts/base.py.
Import VoiceService directly:
  from beta.interaction.voice.service import VoiceService
"""

from beta.interaction.voice.contracts import (
    SpeechArtifact,
    SpeechRequest,
    VoicePipelineResult,
)
from beta.interaction.voice.errors import (
    ProviderNotReadyError,
    VoiceEngineError,
    ProfileResolutionError,
)

__all__ = [
    "SpeechRequest",
    "SpeechArtifact",
    "VoicePipelineResult",
    "VoiceEngineError",
    "ProviderNotReadyError",
    "ProfileResolutionError",
]
