"""
infrastructure/character_assets/sources/inspectors.py

Inspectors for different local asset sources.
Each inspector yields discovered assets and evidence about canonical identity.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Iterator

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
        metadata: dict | None = None,
    ):
        self.source_path = source_path
        self.relative_path = relative_path
        self.source_type = source_type
        self.detected_type = detected_type
        self.size_bytes = size_bytes
        self.checksum = checksum
        self.metadata = metadata or {}
        
    def to_dict(self) -> dict:
        return {
            "source_path": str(self.source_path),
            "relative_source_path": self.relative_path,
            "source_type": self.source_type,
            "detected_type": self.detected_type,
            "size_bytes": self.size_bytes,
            "checksum": self.checksum,
            "metadata": self.metadata,
        }


class BaseInspector:
    """Base class for source inspectors."""
    source_type = "unknown"
    
    def __init__(self, root_path: Path):
        self.root_path = root_path.resolve(strict=True)
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
                if path.name == ".gitkeep":
                    continue
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
                    
                metadata = self._inspect_asset_metadata(path, rel_path, category)
                asset = ScannedAsset(
                    source_path=path,
                    relative_path=str(rel_path),
                    source_type=self.source_type,
                    detected_type=category,
                    size_bytes=path.stat().st_size,
                    checksum=checksum,
                    metadata=metadata,
                )
                assets.append(asset)
                
                # Extract evidence (custom per inspector)
                ev = self._extract_evidence(path, rel_path, asset)
                if asset.metadata.get("character_metadata_value"):
                    ev.append({
                        "source_name": self.source_type,
                        "value": asset.metadata["character_metadata_value"],
                        "confidence": "high",
                        "context": f"Character metadata in {rel_path}",
                    })
                if ev:
                    evidence.extend(ev)
                    
        except Exception as e:
            logger.error(f"Inspection failed for {self.root_path}: {e}")
            
        return assets, evidence

    def _extract_evidence(self, path: Path, rel_path: Path, asset: ScannedAsset) -> list[dict]:
        """Override to extract identity evidence from specific files."""
        return []

    def _inspect_asset_metadata(self, path: Path, rel_path: Path, category: str) -> dict:
        """Return read-only inspection details without copying or modifying files."""
        lower_name = path.name.lower()
        details: dict[str, Any] = {
            "provenance": "local_read_only_inspection",
        }

        if category == "voice_candidate":
            details["reference_kind"] = "audio"
            if any(marker in lower_name for marker in ("song", "sing", "music", "bgm")):
                details.setdefault("warnings", []).append(
                    "filename suggests song/music; do not use as a neutral reference without review"
                )
            return details

        if category not in ("metadata_candidate", "transcript_candidate"):
            return details

        text = ""
        if path.stat().st_size <= 5 * 1024 * 1024:
            try:
                text = path.read_text(encoding="utf-8-sig", errors="ignore")
            except OSError:
                text = ""

        data: Any = None
        if path.suffix.lower() == ".json" and text:
            try:
                data = json.loads(text)
            except json.JSONDecodeError:
                data = None

        flat_values = list(_walk_scalar_values(data)) if data is not None else []
        flat_keys = set(_walk_keys(data)) if data is not None else set()
        joined_name_keys = " ".join(sorted(flat_keys)).lower() + " " + lower_name

        roles = []
        if any(token in joined_name_keys for token in ("character", "chara", "profile")):
            roles.append("character_metadata")
        if any(token in joined_name_keys for token in ("animation", "motion")):
            roles.append("animation_metadata")
        if any(token in joined_name_keys for token in ("emote", "emotion", "expression", "face")):
            roles.append("emote_metadata")
        if any(token in joined_name_keys for token in ("sound", "voice", "audio", "cue")):
            roles.append("sound_mapping")
        if category == "transcript_candidate" or any(
            token in joined_name_keys for token in ("transcript", "subtitle", "text", "line")
        ):
            roles.append("transcript_metadata")

        referenced_audio = [
            str(value)
            for value in flat_values
            if isinstance(value, str)
            and Path(value).suffix.lower() in {".wav", ".ogg", ".flac", ".mp3", ".acb", ".awb"}
        ]
        referenced_transcripts = [
            str(value)
            for value in flat_values
            if isinstance(value, str)
            and Path(value).suffix.lower() in {".txt", ".csv", ".tsv", ".json"}
            and "transcript" in str(value).lower()
        ]

        if roles:
            details["metadata_roles"] = sorted(set(roles))
        if referenced_audio:
            details["referenced_audio"] = sorted(set(referenced_audio))
        if referenced_transcripts:
            details["referenced_transcripts"] = sorted(set(referenced_transcripts))

        transcript_text = _first_value_for_keys(
            data, {"transcript", "text", "line", "subtitle", "caption"}
        )
        if isinstance(transcript_text, str) and transcript_text.strip():
            details["transcript_present"] = True
            details["transcript_preview"] = transcript_text.strip()[:120]

        character_id = _first_value_for_keys(
            data, {"character_id", "chara_id", "character_name", "character", "name"}
        )
        if isinstance(character_id, (str, int)):
            details["character_metadata_value"] = str(character_id)

        return details


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
                data = json.loads(path.read_text(encoding="utf-8-sig", errors="ignore"))
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


def _walk_scalar_values(value: Any) -> Iterator[Any]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_scalar_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_scalar_values(item)
    else:
        yield value


def _walk_keys(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_keys(item)


def _first_value_for_keys(value: Any, keys: set[str]) -> Any:
    if isinstance(value, dict):
        for key, item in value.items():
            if str(key).lower() in keys:
                return item
            found = _first_value_for_keys(item, keys)
            if found is not None:
                return found
    elif isinstance(value, list):
        for item in value:
            found = _first_value_for_keys(item, keys)
            if found is not None:
                return found
    return None
