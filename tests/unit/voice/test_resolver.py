import json
from pathlib import Path

import pytest
from beta.interaction.voice.contracts import ReadinessStatus
from beta.interaction.voice.resolver import VoiceProfileResolver


def test_resolver_no_models(tmp_path: Path):
    # Setup fakes
    profiles_dir = tmp_path / "profiles" / "characters" / "mambo"
    profiles_dir.mkdir(parents=True)
    char_md = profiles_dir / "CHARACTER.md"
    char_md.write_text("**Display Alias:** Mambo\n**Canonical Character:** \u2705 VERIFIED", encoding="utf-8")
    
    resolver = VoiceProfileResolver(tmp_path)
    profile = resolver.resolve("mambo")
    
    assert profile.persona_alias == "Mambo"
    assert profile.canonical_identity_status == "verified"
    assert profile.readiness_status == ReadinessStatus.FALLBACK_READY
    assert not profile.model_paths


def test_resolver_with_rvc_model(tmp_path: Path):
    profiles_dir = tmp_path / "profiles" / "characters" / "mambo"
    profiles_dir.mkdir(parents=True)
    (profiles_dir / "CHARACTER.md").write_text("", encoding="utf-8")
    
    metadata_dir = tmp_path / "var" / "assets" / "characters" / "mambo" / "metadata"
    metadata_dir.mkdir(parents=True)
    
    manifest = [
        {
            "import_status": "imported",
            "asset_type": "rvc_candidate",
            "destination_path": "var/assets/characters/mambo/models/rvc/mambo.pth",
            "provenance": "test"
        }
    ]
    (metadata_dir / "import-manifest_1.json").write_text(json.dumps(manifest), encoding="utf-8")
    
    resolver = VoiceProfileResolver(tmp_path)
    profile = resolver.resolve("mambo")
    
    assert profile.readiness_status == ReadinessStatus.BLOCKED
    assert profile.model_paths["rvc"] == "var/assets/characters/mambo/models/rvc/mambo.pth"
    assert len(profile.warnings) == 1
    assert "untrusted_not_loaded" in profile.warnings[0]


def test_resolver_profile_not_found(tmp_path: Path):
    resolver = VoiceProfileResolver(tmp_path)
    with pytest.raises(ValueError, match="Profile not found"):
        resolver.resolve("unknown")
