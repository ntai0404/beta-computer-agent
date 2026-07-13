"""
interaction/voice/resolver.py

Resolves voice profiles by reading character metadata, assets, and voice hints.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from beta.interaction.voice.contracts import (
    PipelinePreference,
    ReadinessStatus,
    ResolvedVoiceProfile,
    VoiceHint,
)

logger = logging.getLogger(__name__)


class VoiceProfileResolver:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.profiles_dir = project_root / "profiles" / "characters"
        self.assets_dir = project_root / "var" / "assets" / "characters"

    def resolve(self, profile_id: str) -> ResolvedVoiceProfile:
        char_dir = self.profiles_dir / profile_id
        if not char_dir.exists():
            raise ValueError(f"Profile not found: {profile_id}")

        char_md_path = char_dir / "CHARACTER.md"
        alias = profile_id
        canonical_status = "unresolved"
        
        if char_md_path.exists():
            content = char_md_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                if "**Display Alias:**" in line:
                    alias = line.split("**Display Alias:**")[1].strip()
                if "**Canonical Character:**" in line:
                    if "VERIFIED" in line:
                        canonical_status = "verified"
                    elif "CANDIDATE" in line:
                        canonical_status = "candidate"
                    else:
                        canonical_status = "unresolved"

        # Check imported assets
        metadata_dir = self.assets_dir / profile_id / "metadata"
        models: dict[str, str] = {}
        provenance: dict[str, str] = {}
        has_rvc = False
        has_direct_tts = False
        
        if metadata_dir.exists():
            manifests = list(metadata_dir.glob("import-manifest_*.json"))
            if manifests:
                # Use latest manifest
                latest_manifest = sorted(manifests)[-1]
                try:
                    entries = json.loads(latest_manifest.read_text(encoding="utf-8"))
                    for entry in entries:
                        if entry.get("import_status") in ("imported", "already_present"):
                            a_type = entry.get("asset_type")
                            if a_type == "rvc_candidate":
                                has_rvc = True
                                models["rvc"] = entry.get("destination_path")
                                provenance["rvc"] = entry.get("provenance", "unknown")
                except Exception as e:
                    logger.error(f"Failed to read manifest {latest_manifest}: {e}")

        # Determine Readiness Status
        readiness = ReadinessStatus.FALLBACK_READY
        
        # We do not have a mechanism to mark models as trusted yet.
        # So even if we have an RVC model, it is blocked for now.
        if has_rvc:
            readiness = ReadinessStatus.BLOCKED

        warnings = []
        if readiness == ReadinessStatus.BLOCKED:
            warnings.append(f"Imported RVC model found for '{profile_id}', but it is marked as untrusted_not_loaded. Falling back.")

        return ResolvedVoiceProfile(
            profile_id=profile_id,
            character_profile_id=profile_id,
            persona_alias=alias,
            canonical_identity_status=canonical_status,
            selected_pipeline=PipelinePreference.AUTO, # To be overridden by pipeline selector
            selected_tts_provider="windows-system",
            selected_conversion_provider=None,
            selected_voice_name=None,
            voice_hint=VoiceHint(),  # Stub for now
            model_paths=models,
            provenance=provenance,
            warnings=warnings,
            readiness_status=readiness
        )
