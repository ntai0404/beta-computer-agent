"""
infrastructure/character_assets/importers/planner.py

Orchestrates local source inspection.
Generates asset inventories, identity evidence, pipeline recommendations,
and the final import plan proposals.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from beta.infrastructure.character_assets.metadata.identity import IdentityResolver
from beta.infrastructure.character_assets.metadata.pipeline import VoicePipelineRecommender
from beta.infrastructure.character_assets.sources.inspectors import (
    DesktopGremlinInspector,
    GameDataInspector,
    RvcModelInspector,
    VoiceDatasetInspector,
)

logger = logging.getLogger(__name__)


class ImportPlanner:
    def __init__(self, profile_id: str, persona_alias: str, artifacts_dir: Path):
        self.profile_id = profile_id
        self.persona_alias = persona_alias
        self.artifacts_dir = artifacts_dir
        self.output_dir = artifacts_dir / "character-inspection" / profile_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.identity_resolver = IdentityResolver(persona_alias)
        self.all_assets = []
        self.warnings = []

    def inspect_sources(
        self,
        desktop_gremlin_path: Optional[Path] = None,
        game_data_path: Optional[Path] = None,
        voice_dataset_path: Optional[Path] = None,
        rvc_model_path: Optional[Path] = None,
    ) -> None:
        """Run all requested inspectors."""
        
        inspectors_to_run = []
        
        if desktop_gremlin_path:
            inspectors_to_run.append(DesktopGremlinInspector(desktop_gremlin_path))
        if game_data_path:
            inspectors_to_run.append(GameDataInspector(game_data_path))
        if voice_dataset_path:
            inspectors_to_run.append(VoiceDatasetInspector(voice_dataset_path))
        if rvc_model_path:
            inspectors_to_run.append(RvcModelInspector(rvc_model_path))

        for inspector in inspectors_to_run:
            logger.info(f"Running {inspector.__class__.__name__} on {inspector.root_path}")
            assets, evidence = inspector.inspect()
            self.all_assets.extend(assets)
            
            for ev in evidence:
                self.identity_resolver.add_evidence(
                    source_name=ev["source_name"],
                    value=ev["value"],
                    confidence=ev["confidence"],
                    context=ev["context"]
                )

    def generate_reports(self) -> None:
        """Write all JSON and MD reports based on gathered data."""
        
        # 1. Identity Resolution
        status, canonical_id = self.identity_resolver.resolve()
        
        identity_report = {
            "persona_alias": self.persona_alias,
            "resolution_status": status.value,
            "canonical_character_id": canonical_id,
            "evidence": self.identity_resolver.get_all_evidence()
        }
        self._write_json("identity-evidence.json", identity_report)

        # 2. Pipeline Recommendation
        inventory_dicts = [a.to_dict() for a in self.all_assets]
        recommender = VoicePipelineRecommender(inventory_dicts)
        recommendation = recommender.recommend()

        # 3. Categorized Inventories
        avatar_inv = [a for a in inventory_dicts if a["detected_type"] == "avatar_candidate"]
        voice_inv = [a for a in inventory_dicts if a["detected_type"] == "voice_candidate"]
        transcript_inv = [a for a in inventory_dicts if a["detected_type"] == "transcript_candidate"]
        model_inv = [a for a in inventory_dicts if a["detected_type"] == "rvc_candidate"]
        
        self._write_json("avatar-inventory.json", avatar_inv)
        self._write_json("voice-inventory.json", voice_inv)
        self._write_json("transcript-inventory.json", transcript_inv)
        self._write_json("model-inventory.json", model_inv)
        self._write_json(
            "inspection-details.json",
            {
                "character_metadata": _assets_with_role(inventory_dicts, "character_metadata"),
                "animation_metadata": _assets_with_role(inventory_dicts, "animation_metadata"),
                "emote_metadata": _assets_with_role(inventory_dicts, "emote_metadata"),
                "sound_mapping": _assets_with_role(inventory_dicts, "sound_mapping"),
                "referenced_audio": _referenced_values(inventory_dicts, "referenced_audio"),
                "referenced_transcripts": _referenced_values(
                    inventory_dicts, "referenced_transcripts"
                ),
            },
        )
        voice_reference_candidates = _voice_reference_candidates(
            voice_inv,
            inventory_dicts,
            canonical_id,
        )
        self._write_json("voice-reference-candidates.json", voice_reference_candidates)

        # 4. Import Plan Proposal
        import_plan = []
        for asset in self.all_assets:
            dest_dir = "unknown"
            if asset.detected_type == "avatar_candidate":
                dest_dir = "avatar"
            elif asset.detected_type == "voice_candidate":
                dest_dir = "references/audio"
            elif asset.detected_type == "transcript_candidate":
                dest_dir = "transcripts"
            elif asset.detected_type == "rvc_candidate":
                dest_dir = "models/rvc"
                
            dest_path = f"var/assets/characters/{self.profile_id}/{dest_dir}/{asset.source_path.name}"
            
            manifest_entry = {
                "source_type": asset.source_type,
                "source_path": str(asset.source_path),
                "imported_at": None, # Not imported yet
                "canonical_character_id": canonical_id,
                "persona_alias": self.persona_alias,
                "asset_type": asset.detected_type,
                "original_filename": asset.source_path.name,
                "destination_path": dest_path,
                "checksum": asset.checksum,
                "license_note": "User-supplied external asset.",
                "provenance": "Local file inspection.",
                "validation_status": "pending_approval"
            }
            import_plan.append(manifest_entry)
            
        self._write_json("import-plan.json", import_plan)

        # 5. Profile Update Proposal
        profile_proposal = {
            "profile_id": self.profile_id,
            "persona_alias": self.persona_alias,
            "canonical_character_id": canonical_id,
            "canonical_identity_status": status.value,
        }
        self._write_json("profile-update-proposal.json", profile_proposal)

        # 6. Inspection Summary
        summary = {
            "profile_id": self.profile_id,
            "inspected_at": datetime.now(timezone.utc).isoformat(),
            "total_assets_found": len(self.all_assets),
            "asset_counts": {
                "avatars": len(avatar_inv),
                "voices": len(voice_inv),
                "transcripts": len(transcript_inv),
                "models": len(model_inv),
            },
            "identity_status": status.value,
            "voice_pipeline_recommendation": recommendation,
            "voice_reference_status": voice_reference_candidates["status"],
        }
        self._write_json("inspection-summary.json", summary)

        # 7. Warnings Markdown
        warnings_md = "# Inspection Warnings\n\n"
        if not self.warnings:
            warnings_md += "No warnings.\n"
        else:
            for w in self.warnings:
                warnings_md += f"- {w}\n"
        (self.output_dir / "warnings.md").write_text(warnings_md, encoding="utf-8")

    def _write_json(self, filename: str, data: dict | list) -> None:
        path = self.output_dir / filename
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        logger.info(f"Wrote report: {path}")


def _assets_with_role(inventory: list[dict], role: str) -> list[dict]:
    return [
        asset
        for asset in inventory
        if role in asset.get("metadata", {}).get("metadata_roles", [])
    ]


def _referenced_values(inventory: list[dict], metadata_key: str) -> list[dict]:
    references = []
    for asset in inventory:
        for value in asset.get("metadata", {}).get(metadata_key, []):
            references.append({
                "declared_in": asset["relative_source_path"],
                "value": value,
                "source_type": asset["source_type"],
                "provenance": asset.get("metadata", {}).get("provenance"),
            })
    return references


def _voice_reference_candidates(
    voice_inventory: list[dict],
    full_inventory: list[dict],
    canonical_id: str | None,
) -> dict:
    mapped_audio_names = set()
    transcript_names = set()
    for asset in full_inventory:
        metadata = asset.get("metadata", {})
        for ref in metadata.get("referenced_audio", []):
            mapped_audio_names.add(Path(ref).name.lower())
        if metadata.get("transcript_present") or "transcript_metadata" in metadata.get(
            "metadata_roles", []
        ):
            transcript_names.add(Path(asset["relative_source_path"]).stem.lower())

    candidates = []
    usable_count = 0
    for asset in voice_inventory:
        filename = Path(asset["relative_source_path"]).name.lower()
        stem = Path(filename).stem.lower()
        evidence = []
        warnings = list(asset.get("metadata", {}).get("warnings", []))

        if filename in mapped_audio_names:
            evidence.append("referenced_by_sound_mapping")
        if stem in transcript_names:
            evidence.append("matching_transcript_metadata")
        if canonical_id and evidence:
            evidence.append("canonical_identity_from_metadata")

        usable = bool(evidence)
        if usable:
            usable_count += 1
        else:
            warnings.append(
                "not usable as a voice reference yet: filename alone is not sufficient evidence"
            )

        candidates.append({
            "source_path": asset["source_path"],
            "relative_source_path": asset["relative_source_path"],
            "checksum": asset["checksum"],
            "size_bytes": asset["size_bytes"],
            "usable": usable,
            "evidence": evidence,
            "warnings": warnings,
            "provenance": "local_read_only_inspection",
        })

    return {
        "status": "usable_found" if usable_count else "none_found",
        "usable_count": usable_count,
        "total_audio_candidates": len(voice_inventory),
        "candidates": candidates,
    }
