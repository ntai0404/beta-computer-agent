"""
interaction/voice/errors.py

Domain-level errors raised by the Voice Interaction layer.

These exceptions are what callers (CLI, Primary Agent, tests) receive.
They carry no provider-specific types or messages.
"""


class VoiceError(Exception):
    """Base class for all voice interaction errors."""


class SpeechRequestValidationError(VoiceError):
    """Raised when a SpeechRequest fails validation."""


class TtsProviderError(VoiceError):
    """
    Raised when the TTS provider fails to synthesize audio.

    Wraps the underlying provider error without leaking implementation details.
    """


class PlaybackError(VoiceError):
    """Raised when audio playback fails."""


class VoiceProfileNotFoundError(VoiceError):
    """Raised when the requested voice profile does not exist."""


class AudioOutputError(VoiceError):
    """Raised when the audio file cannot be written or found."""
