"""
infrastructure/character_assets/importers/rollback.py

Rollback manager for imported assets.
Deletes files created during an import batch based on the rollback manifest.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from beta.infrastructure.character_assets.validation.security import compute_sha256, is_path_safe

logger = logging.getLogger(__name__)


class RollbackManager:
    def __init__(self, profile_id: str):
        self.profile_id = profile_id
        
        _PROJECT_ROOT = Path(__file__).resolve().parents[4]
        self.assets_root = _PROJECT_ROOT / "var" / "assets" / "characters" / profile_id
        
    def rollback(self, rollback_manifest_path: Path) -> dict:
        """
        Executes a rollback based on the manifest.
        Returns a summary of actions taken.
        """
        if not rollback_manifest_path.exists():
            raise FileNotFoundError(f"Rollback manifest not found: {rollback_manifest_path}")
            
        try:
            manifest_entries = json.loads(rollback_manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse rollback manifest: {e}")
            
        results = {
            "deleted": [],
            "skipped_missing": [],
            "skipped_checksum_mismatch": [],
            "failed": []
        }
        
        for entry in manifest_entries:
            dest_path_str = entry.get("destination_path")
            expected_checksum = entry.get("checksum")
            
            if not dest_path_str or not expected_checksum:
                logger.warning(f"Invalid rollback entry: {entry}")
                results["failed"].append({"entry": entry, "reason": "Missing required fields"})
                continue
                
            dest_path = Path(dest_path_str)
            if not dest_path.is_absolute():
                _PROJECT_ROOT = Path(__file__).resolve().parents[4]
                dest_path = _PROJECT_ROOT / dest_path
                
            # Security check: must be inside assets_root
            if not is_path_safe(self.assets_root, dest_path):
                logger.warning(f"Rollback blocked (outside profile assets root): {dest_path}")
                results["failed"].append({"path": str(dest_path), "reason": "Path escape attempt"})
                continue
                
            if not dest_path.exists():
                logger.info(f"Rollback skipped (file already missing): {dest_path}")
                results["skipped_missing"].append(str(dest_path))
                continue
                
            # Verify checksum before deletion to prevent deleting files modified after import
            try:
                current_checksum = compute_sha256(dest_path)
            except Exception as e:
                logger.error(f"Failed to compute checksum for rollback {dest_path}: {e}")
                results["failed"].append({"path": str(dest_path), "reason": f"Checksum error: {e}"})
                continue
                
            if current_checksum != expected_checksum:
                logger.warning(f"Rollback skipped (checksum mismatch, file was modified): {dest_path}")
                results["skipped_checksum_mismatch"].append(str(dest_path))
                continue
                
            # Delete file
            try:
                dest_path.unlink()
                logger.info(f"Rollback deleted: {dest_path}")
                results["deleted"].append(str(dest_path))
            except Exception as e:
                logger.error(f"Failed to delete {dest_path}: {e}")
                results["failed"].append({"path": str(dest_path), "reason": f"Delete error: {e}"})
                
        return results
