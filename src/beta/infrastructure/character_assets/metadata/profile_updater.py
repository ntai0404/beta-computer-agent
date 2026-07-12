"""
infrastructure/character_assets/metadata/profile_updater.py

Updates the character profile metadata (CHARACTER.md) based on the approved proposal.
"""

from __future__ import annotations

import datetime
import logging
import re
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)


class ProfileUpdater:
    def __init__(self, profile_id: str, artifacts_dir: Path):
        self.profile_id = profile_id
        
        _PROJECT_ROOT = Path(__file__).resolve().parents[4]
        self.profile_dir = _PROJECT_ROOT / "profiles" / "characters" / profile_id
        self.backups_dir = artifacts_dir / "character-import" / profile_id / "backups"
        self.character_md = self.profile_dir / "CHARACTER.md"

    def apply_update(
        self,
        canonical_character_id: str | None,
        canonical_identity_status: str,
        asset_counts: dict[str, int]
    ) -> bool:
        """
        Backs up the existing CHARACTER.md, then applies the updates.
        Returns True if updated, False if not.
        """
        if not self.character_md.exists():
            logger.warning(f"Profile file not found: {self.character_md}")
            return False

        # Backup
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backups_dir / f"CHARACTER_{timestamp}.md.bak"
        shutil.copy2(self.character_md, backup_path)
        logger.info(f"Backed up profile to: {backup_path}")

        # Apply update
        content = self.character_md.read_text(encoding="utf-8")
        
        # Update canonical fields at the top
        status_str = canonical_identity_status.upper()
        if canonical_identity_status == "verified":
            status_str = f"✅ {status_str}"
        elif canonical_identity_status == "candidate":
            status_str = f"⏳ {status_str}"
        else:
            status_str = f"⚠️ {status_str}"
            
        char_val = canonical_character_id if canonical_character_id else "⚠️ UNRESOLVED"
        
        content = re.sub(
            r"\*\*Canonical Character:\*\*.*",
            f"**Canonical Character:** {status_str}",
            content
        )
        content = re.sub(
            r"\*\*Canonical Character ID:\*\*.*",
            f"**Canonical Character ID:** {char_val}",
            content
        )
        content = re.sub(
            r"\*\*Source Status:\*\*.*",
            f"**Source Status:** Checked at {datetime.datetime.now().strftime('%Y-%m-%d')}",
            content
        )
        
        # Update status table
        content = self._update_table_row(content, "Canonical character name", status_str)
        content = self._update_table_row(content, "Canonical character ID", char_val)
        
        av_status = "Imported" if asset_counts.get("avatars", 0) > 0 else "Not imported"
        content = self._update_table_row(content, "Avatar asset", av_status)
        
        vc_status = "Imported" if asset_counts.get("voices", 0) > 0 else "Not imported"
        content = self._update_table_row(content, "Voice references", vc_status)
        
        tr_status = "Imported" if asset_counts.get("transcripts", 0) > 0 else "Not imported"
        content = self._update_table_row(content, "Transcripts", tr_status)
        
        md_status = "imported_untrusted_not_loaded" if asset_counts.get("models", 0) > 0 else "Not available"
        content = self._update_table_row(content, "Voice conversion model (RVC)", md_status)

        # Append to update history
        history_entry = f"| {datetime.datetime.now().strftime('%Y-%m')} | Asset import and identity resolution | import_character_assets |\n"
        content += history_entry

        self.character_md.write_text(content, encoding="utf-8")
        logger.info(f"Updated profile: {self.character_md}")
        return True

    def _update_table_row(self, content: str, key: str, new_val: str) -> str:
        # Example row: | Canonical character name | **Unresolved** |
        pattern = r"(\| " + re.escape(key) + r" \| ).*?( \|)"
        return re.sub(pattern, rf"\1**{new_val}**\2", content)
