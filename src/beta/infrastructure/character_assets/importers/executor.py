"""
infrastructure/character_assets/importers/executor.py

Executes the approved character asset import plan.
Performs atomic copying, revalidates checksums, and handles conflicts.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import shutil
from pathlib import Path

from beta.infrastructure.character_assets.validation.security import compute_sha256, is_path_safe

logger = logging.getLogger(__name__)


class ImportExecutor:
    def __init__(self, profile_id: str, import_plan_path: Path, artifacts_dir: Path):
        self.profile_id = profile_id
        self.import_plan_path = import_plan_path
        self.artifacts_dir = artifacts_dir
        
        self.import_dir = artifacts_dir / "character-import" / profile_id
        self.import_dir.mkdir(parents=True, exist_ok=True)
        
        _PROJECT_ROOT = Path(__file__).resolve().parents[4]
        self.assets_root = _PROJECT_ROOT / "var" / "assets" / "characters" / profile_id
        self.assets_root.mkdir(parents=True, exist_ok=True)
        self.project_root = _PROJECT_ROOT

    def execute(self, approved_asset_paths: list[str], dry_run: bool = False) -> dict:
        """
        Executes the import plan for the approved assets.
        approved_asset_paths should be relative paths as specified in the import plan (original_filename or relative_source_path if added).
        We will match based on original_filename for simplicity in this implementation.
        """
        if not self.import_plan_path.exists():
            raise FileNotFoundError(f"Import plan not found: {self.import_plan_path}")
            
        import_plan = json.loads(self.import_plan_path.read_text(encoding="utf-8"))
        
        results = {
            "imported": [],
            "already_present": [],
            "skipped": [],
            "conflict": [],
            "failed": []
        }
        
        provenance_manifest = []
        rollback_manifest = []
        
        total_bytes_copied = 0
        
        for entry in import_plan:
            original_filename = entry.get("original_filename")
            
            if original_filename not in approved_asset_paths:
                results["skipped"].append(original_filename)
                entry["import_status"] = "skipped"
                provenance_manifest.append(entry)
                continue
                
            source_path = Path(entry["source_path"])
            dest_path_str = entry["destination_path"]
            
            dest_path = Path(dest_path_str)
            if not dest_path.is_absolute():
                dest_path = self.project_root / dest_path
                
            expected_checksum = entry["checksum"]
            
            # 1. Validation before copy
            if not source_path.exists():
                results["failed"].append({"file": original_filename, "reason": "Source file vanished"})
                entry["import_status"] = "failed"
                provenance_manifest.append(entry)
                continue
                
            if not is_path_safe(self.assets_root, dest_path):
                results["failed"].append({"file": original_filename, "reason": "Destination escape attempt"})
                entry["import_status"] = "failed"
                provenance_manifest.append(entry)
                continue
                
            # 2. Revalidate source checksum
            try:
                current_source_checksum = compute_sha256(source_path)
            except Exception as e:
                results["failed"].append({"file": original_filename, "reason": f"Source read error: {e}"})
                entry["import_status"] = "failed"
                provenance_manifest.append(entry)
                continue
                
            if current_source_checksum != expected_checksum:
                results["failed"].append({"file": original_filename, "reason": "Source checksum changed since inspection"})
                entry["import_status"] = "failed"
                provenance_manifest.append(entry)
                continue
                
            # 3. Check destination conflict
            if dest_path.exists():
                existing_checksum = compute_sha256(dest_path)
                if existing_checksum == expected_checksum:
                    results["already_present"].append(original_filename)
                    entry["import_status"] = "already_present"
                    provenance_manifest.append(entry)
                    continue
                else:
                    results["conflict"].append({"file": original_filename, "dest": str(dest_path)})
                    entry["import_status"] = "conflict"
                    provenance_manifest.append(entry)
                    continue
                    
            # 4. Atomic Copy
            if not dry_run:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                temp_path = dest_path.with_suffix(".tmp_import")
                
                try:
                    shutil.copy2(source_path, temp_path)
                    temp_checksum = compute_sha256(temp_path)
                    
                    if temp_checksum != expected_checksum:
                        raise ValueError("Temp file checksum mismatch after copy")
                        
                    # Atomic rename
                    os.replace(temp_path, dest_path)
                    
                    results["imported"].append(original_filename)
                    total_bytes_copied += source_path.stat().st_size
                    
                    entry["import_status"] = "imported"
                    entry["imported_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                    
                    if entry.get("asset_type") == "rvc_candidate":
                        entry["model_status"] = "imported_untrusted_not_loaded"
                        
                    provenance_manifest.append(entry)
                    
                    rollback_manifest.append({
                        "destination_path": str(dest_path),
                        "checksum": expected_checksum
                    })
                    
                except Exception as e:
                    if temp_path.exists():
                        try:
                            temp_path.unlink()
                        except OSError:
                            pass
                    results["failed"].append({"file": original_filename, "reason": f"Copy error: {e}"})
                    entry["import_status"] = "failed"
                    provenance_manifest.append(entry)
            else:
                # Dry run
                results["imported"].append(original_filename)
                total_bytes_copied += source_path.stat().st_size
                entry["import_status"] = "imported (dry-run)"
                provenance_manifest.append(entry)
                
        # Write reports
        prefix = "dry-run-" if dry_run else ""
        
        summary = {
            "status": "dry_run" if dry_run else "completed",
            "imported_count": len(results["imported"]),
            "already_present_count": len(results["already_present"]),
            "skipped_count": len(results["skipped"]),
            "conflict_count": len(results["conflict"]),
            "failed_count": len(results["failed"]),
            "total_bytes_copied": total_bytes_copied
        }
        
        self._write_json(f"{prefix}import-summary.json", summary)
        self._write_json(f"{prefix}import-results.json", results)
        
        if not dry_run:
            self._write_json("rollback-manifest.json", rollback_manifest)
            
            # Write provenance manifest to the metadata dir
            metadata_dir = self.assets_root / "metadata"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            manifest_path = metadata_dir / f"import-manifest_{timestamp}.json"
            manifest_path.write_text(json.dumps(provenance_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
            
        return results

    def _write_json(self, filename: str, data: dict | list) -> None:
        path = self.import_dir / filename
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Wrote report: {path}")
