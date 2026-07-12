"""
apps/cli/import_character_assets.py

CLI for approving and importing character assets into Beta's internal storage.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.character_assets.importers.executor import ImportExecutor
from beta.infrastructure.character_assets.importers.rollback import RollbackManager
from beta.infrastructure.character_assets.metadata.pipeline import VoicePipelineRecommender
from beta.infrastructure.character_assets.metadata.profile_updater import ProfileUpdater

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def cmd_rollback(profile: str, rollback_manifest: Path) -> int:
    manager = RollbackManager(profile)
    try:
        results = manager.rollback(rollback_manifest)
        print("\nRollback complete.")
        print(f"Deleted: {len(results['deleted'])}")
        print(f"Skipped (missing): {len(results['skipped_missing'])}")
        print(f"Skipped (modified): {len(results['skipped_checksum_mismatch'])}")
        print(f"Failed: {len(results['failed'])}")
        if results['failed']:
            for f in results['failed']:
                print(f"  - {f}", file=sys.stderr)
        return 0 if not results['failed'] else 1
    except Exception as e:
        print(f"Rollback failed: {e}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="import_character_assets",
        description="Beta Computer Agent — Safe Asset Import CLI",
    )
    parser.add_argument("--profile", required=True, help="Profile ID (e.g. 'mambo')")
    parser.add_argument("--plan", type=Path, help="Path to import-plan.json")
    parser.add_argument("--approve-file", type=Path, help="Path to JSON file containing approved asset IDs")
    parser.add_argument("--approve-id", action="append", default=[], help="Asset ID (original filename) to approve")
    parser.add_argument("--dry-run", action="store_true", help="Simulate import without copying files")
    parser.add_argument("--apply-profile-update", action="store_true", help="Apply proposed profile updates")
    parser.add_argument("--rollback", type=Path, help="Path to rollback-manifest.json to revert an import")

    args = parser.parse_args()

    if args.rollback:
        return cmd_rollback(args.profile, args.rollback)

    if not args.plan:
        print("Error: --plan is required unless running --rollback", file=sys.stderr)
        return 1

    artifacts_dir = _PROJECT_ROOT / "var" / "artifacts"
    
    # Gather approvals
    approved_ids = set(args.approve_id)
    if args.approve_file:
        try:
            approve_data = json.loads(args.approve_file.read_text(encoding="utf-8"))
            if approve_data.get("profile_id") != args.profile:
                print("Error: approve-file profile_id does not match --profile", file=sys.stderr)
                return 1
            approved_ids.update(approve_data.get("approved_asset_ids", []))
            if approve_data.get("apply_profile_update"):
                args.apply_profile_update = True
        except Exception as e:
            print(f"Error reading approve-file: {e}", file=sys.stderr)
            return 1

    if not approved_ids:
        print("Error: No assets approved. Use --approve-id or --approve-file.", file=sys.stderr)
        return 1

    # Execute import
    executor = ImportExecutor(args.profile, args.plan, artifacts_dir)
    try:
        print(f"Starting {'DRY RUN ' if args.dry_run else ''}import for {args.profile}...")
        results = executor.execute(list(approved_ids), dry_run=args.dry_run)
        
        print(f"\nImport Results:")
        print(f"Imported       : {len(results['imported'])}")
        print(f"Already present: {len(results['already_present'])}")
        print(f"Skipped        : {len(results['skipped'])}")
        print(f"Conflicts      : {len(results['conflict'])}")
        print(f"Failed         : {len(results['failed'])}")
        
        if results['failed']:
            print("\nFailures:", file=sys.stderr)
            for f in results['failed']:
                print(f"  - {f}", file=sys.stderr)

    except Exception as e:
        print(f"Import failed: {e}", file=sys.stderr)
        return 2

    # Post-import Profile Update
    if not args.dry_run and args.apply_profile_update:
        profile_proposal_path = executor.import_dir / "profile-update-proposal.json"
        if profile_proposal_path.exists():
            proposal = json.loads(profile_proposal_path.read_text(encoding="utf-8"))
            
            updater = ProfileUpdater(args.profile, artifacts_dir)
            
            # Asset counts to show in profile
            asset_counts = {
                "avatars": len([a for a in results["imported"] + results["already_present"] if a.endswith((".png", ".jpg", ".json"))]),
                "voices": len([a for a in results["imported"] + results["already_present"] if a.endswith(".wav")]),
                "transcripts": len([a for a in results["imported"] + results["already_present"] if a.endswith((".csv", ".tsv"))]),
                "models": len([a for a in results["imported"] + results["already_present"] if a.endswith(".pth")]),
            }
            
            updated = updater.apply_update(
                canonical_character_id=proposal.get("canonical_character_id"),
                canonical_identity_status=proposal.get("canonical_identity_status"),
                asset_counts=asset_counts
            )
            if updated:
                print("\nProfile updated successfully.")
            else:
                print("\nProfile update skipped or failed.", file=sys.stderr)
        else:
            print("\nProfile update proposal not found. Skipping profile update.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
