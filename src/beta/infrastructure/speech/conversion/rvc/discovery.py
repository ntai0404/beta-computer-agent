"""
infrastructure/speech/conversion/rvc/discovery.py

RVC Voice Conversion Provider (Discovery Only).
Detects RVC models but strictly refuses to load or execute them in this milestone.
"""

from __future__ import annotations

import logging
from pathlib import Path

from beta.interaction.voice.contracts import ResolvedVoiceProfile, SpeechArtifact, VoiceConversionProvider
from beta.interaction.voice.errors import ProviderNotReadyError

logger = logging.getLogger(__name__)


class RvcConversionProvider(VoiceConversionProvider):
    @property
    def provider_id(self) -> str:
        return "rvc-local"

    def inspect_model(self, metadata_only: bool = True) -> dict:
        """Returns capabilities without loading."""
        return {"status": "untrusted_not_loaded"}

    def convert(self, source_audio: Path, target_profile: ResolvedVoiceProfile, output_path: Path) -> SpeechArtifact:
        """
        Refuses to run. 
        Imported models are untrusted and loading .pth is blocked.
        """
        logger.error(f"Attempted to run RVC conversion for {target_profile.profile_id}, but models are untrusted.")
        raise ProviderNotReadyError("RVC models are imported but untrusted. Execution is blocked.")

    def health_check(self) -> bool:
        return False

    def capabilities(self) -> dict:
        return {
            "can_convert": False,
            "reason": "Execution blocked for security."
        }
