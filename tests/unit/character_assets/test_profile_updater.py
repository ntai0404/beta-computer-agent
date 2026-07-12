from pathlib import Path

import pytest
from beta.infrastructure.character_assets.metadata.profile_updater import ProfileUpdater


def test_profile_updater(tmp_path: Path):
    artifacts_dir = tmp_path / "artifacts"
    profile_dir = tmp_path / "profiles" / "characters" / "mambo"
    profile_dir.mkdir(parents=True)
    
    char_md = profile_dir / "CHARACTER.md"
    char_md.write_text("""
**Canonical Character:** ⚠️ UNRESOLVED
**Canonical Character ID:** ⚠️ UNRESOLVED
**Source Status:** Pending verification

| Canonical character name | **Unresolved** |
| Canonical character ID | **Unresolved** |
| Avatar asset | **Not imported** |
""", encoding="utf-8")

    updater = ProfileUpdater("mambo", artifacts_dir)
    # Mock internal paths
    updater.character_md = char_md
    updater.backups_dir = artifacts_dir / "backups"
    
    res = updater.apply_update(
        canonical_character_id="matikanetannhauser",
        canonical_identity_status="verified",
        asset_counts={"avatars": 1}
    )
    
    assert res is True
    
    content = char_md.read_text(encoding="utf-8")
    assert "**Canonical Character:** ✅ VERIFIED" in content
    assert "**Canonical Character ID:** matikanetannhauser" in content
    assert "| Canonical character ID | **matikanetannhauser** |" in content
    assert "| Avatar asset | **Imported** |" in content
    
    # Check backup exists
    backups = list(updater.backups_dir.glob("*.bak"))
    assert len(backups) == 1
