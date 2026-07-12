"""
infrastructure/character_assets/sources/inspectors.py

Inspectors for different local asset sources.
Each inspector yields discovered assets and evidence about canonical identity.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterator

from beta.infrastructure.character_assets.validation.security import (
    SecureScanner,
    categorize_file_by_extension,
    compute_sha256,
)

logger = logging.getLogger(__name__)


class ScannedAsset:
    """Represents a scanned asset before import."""
    def __init__(
        self,
        source_path: Path,
        relative_path: str,
        source_type: str,
        detected_type: str,
        size_bytes: int,
        checksum: str,
    ):
        self.source_path = source_path
        self.relative_path = relative_path
        self.source_type = source_type
        self.detected_type = detected_type
        self.size_bytes = size_bytes
        self.checksum = checksum
        
    def to_dict(self) -> dict:
        return {
            "source_path": str(self.source_path),
            "relative_source_path": self.relative_path,
            "source_type": self.source_type,
            "detected_type": self.detected_type,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
        }


class BaseInspector:
    """Base class for source inspectors."""
    source_type = "unknown"
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.scanner = SecureScanner(root_path)
        
    def inspect(self) -> tuple[list[ScannedAsset], list[dict]]:
        """
        Runs the scanner.
        Returns (assets, evidence_list).
        """
        assets = []
        evidence = []
        
        try:
            for path in self.scanner.scan():
                rel_path = path.relative_to(self.root_path)
                category = categorize_file_by_extension(path)
                
                # Skip blocked files silently, but log warning
                if category == "executable_blocked":
                    logger.warning(f"Blocked executable file: {path}")
                    continue
                    
                # We hash all allowed files
                try:
                    checksum = compute_sha256(path)
                except Exception as e:
                    logger.error(f"Failed to hash {path}: {e}")
                    continue
                    
                asset = ScannedAsset(
                    source_path=path,
                    relative_path=str(rel_path),
                    source_type=self.source_type,
                    detected_type=category,
                    size_bytes=path.stat().st_size,
                    checksum=checksum,
                )
                assets.append(asset)
                
                # Extract evidence (custom per inspector)
                ev = self._extract_evidence(path, rel_path, asset)
                if ev:
                    evidence.extend(ev)
                    
        except Exception as e:
            logger.error(f"Inspection failed for {self.root_path}: {e}")
            
        return assets, evidence

    def _extract_evidence(self, path: Path, rel_path: Path, asset: ScannedAsset) -> list[dict]:
        """Override to extract identity evidence from specific files."""
        return []


class DesktopGremlinInspector(BaseInspector):
    source_type = "desktop-gremlin"
    
    def _extract_evidence(self, path: Path, rel_path: Path, asset: ScannedAsset) -> list[dict]:
        evidence = []
        # If it's inside a folder named like a character (e.g. Models/matikanetannhauser/...)
        parts = rel_path.parts
        if len(parts) > 1 and parts[0].lower() in ("models", "characters"):
            char_folder = parts[1].lower()
            evidence.append({
                "source_name": self.source_type,
                "value": char_folder,
                "confidence": "medium",
                "context": f"Directory name: {char_folder}"
            })
            
        # Inspect config.txt lightly if small
        if path.name.lower() == "config.txt" and asset.size_bytes < 1024 * 1024:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    if "character" in line.lower() or "name" in line.lower():
                        # Rough heuristic
                        if "=" in line:
                            val = line.split("=", 1)[1].strip()
                            if val:
                                evidence.append({
                                    "source_name": self.source_type,
                                    "value": val.lower(),
                                    "confidence": "high",
                                    "context": f"config.txt key-value: {line.strip()}"
                                })
            except Exception:
                pass
                
        return evidence


class VoiceDatasetInspector(BaseInspector):
    source_type = "voice-dataset"
    
    def _extract_evidence(self, path: Path, rel_path: Path, asset: ScannedAsset) -> list[dict]:
        evidence = []
        if path.name.endswith(".json") and asset.size_bytes < 1024 * 1024 * 5:
            # Often voice extractors output a metadata.json
            try:
                data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
                # Looking for character_name or character_id
                if isinstance(data, dict):
                    char_name = data.get("character_name") or data.get("character")
                    if char_name:
                        evidence.append({
                            "source_name": self.source_type,
                            "value": str(char_name).lower(),
                            "confidence": "high",
                            "context": f"Metadata JSON key 'character_name'/'character' in {path.name}"
                        })
            except Exception:
                pass
        return evidence


class RvcModelInspector(BaseInspector):
    source_type = "rvc-model"
    
    def _extract_evidence(self, path: Path, rel_path: Path, asset: ScannedAsset) -> list[dict]:
        evidence = []
        if path.suffix.lower() == ".pth":
            # Just use the filename base as low/medium evidence
            evidence.append({
                "source_name": self.source_type,
                "value": path.stem.lower(),
                "confidence": "medium",
                "context": f"RVC .pth filename: {path.name}"
            })
        return evidence


class GameDataInspector(BaseInspector):
    source_type = "game-data"
    
    def _extract_evidence(self, path: Path, rel_path: Path, asset: ScannedAsset) -> list[dict]:
        return []
