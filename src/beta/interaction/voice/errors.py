"""
interaction/voice/errors.py

Custom exceptions for the Voice Engine.
"""

class VoiceEngineError(Exception):
    """Base exception for Voice Engine errors."""

class ProviderNotReadyError(VoiceEngineError):
    """Raised when a provider is not ready (e.g., untrusted models)."""

class ProfileResolutionError(VoiceEngineError):
    """Raised when a voice profile cannot be resolved."""
