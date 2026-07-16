"""
apps/cli/inspect_character_assets.py

CLI for read-only local character asset inspection.
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

from beta.infrastructure.character_assets.importers.planner import ImportPlanner

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="inspect_character_assets",
        description="Beta Computer Agent — Read-only Local Asset Inspection CLI",
    )
    parser.add_argument(
        "--profile",
        required=True,
        help="Character profile alias (e.g. 'mambo').",
    )
    parser.add_argument(
        "--desktop-gremlin",
        metavar="PATH",
        type=Path,
        help="Local path to Desktop Gremlin or Tracen Academy package.",
    )
    parser.add_argument(
        "--game-data",
        metavar="PATH",
        type=Path,
        help="Local path to UmaViewer or raw game data.",
    )
    parser.add_argument(
        "--voice-dataset",
        metavar="PATH",
        type=Path,
        help="Local path to voice/text extractor output.",
    )
    parser.add_argument(
        "--rvc-model",
        metavar="PATH",
        type=Path,
        help="Local path to RVC model directory.",
    )

    args = parser.parse_args()

    artifacts_dir = _PROJECT_ROOT / "var" / "artifacts"
    
    # Validation
    paths_to_check = [
        args.desktop_gremlin,
        args.game_data,
        args.voice_dataset,
        args.rvc_model
    ]
    
    if not any(paths_to_check):
        print("Error: Must provide at least one local source path.", file=sys.stderr)
        return 1
        
    for p in paths_to_check:
        if p and not p.exists():
            print(f"Error: Source path does not exist: {p}", file=sys.stderr)
            return 1

    try:
        planner = ImportPlanner(
            profile_id=args.profile.lower(),
            persona_alias=args.profile,
            artifacts_dir=artifacts_dir
        )
        
        print(f"Starting inspection for profile: {args.profile}")
        
        planner.inspect_sources(
            desktop_gremlin_path=args.desktop_gremlin,
            game_data_path=args.game_data,
            voice_dataset_path=args.voice_dataset,
            rvc_model_path=args.rvc_model,
        )
        
        print("Generating reports and proposals...")
        planner.generate_reports()
        
        print("\nInspection complete.")
        print(f"Reports written to: {planner.output_dir}")
        summary_path = planner.output_dir / "inspection-summary.json"
        voice_ref_path = planner.output_dir / "voice-reference-candidates.json"
        if summary_path.exists():
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            counts = summary.get("asset_counts", {})
            print("Status:")
            print(f"  total assets        : {summary.get('total_assets_found', 0)}")
            print(f"  avatars             : {counts.get('avatars', 0)}")
            print(f"  voice candidates    : {counts.get('voices', 0)}")
            print(f"  transcripts         : {counts.get('transcripts', 0)}")
            print(f"  models              : {counts.get('models', 0)}")
            print(f"  identity            : {summary.get('identity_status')}")
            print(f"  voice references    : {summary.get('voice_reference_status')}")
        if voice_ref_path.exists():
            voice_refs = json.loads(voice_ref_path.read_text(encoding="utf-8"))
            if voice_refs.get("status") == "none_found":
                print("  usable voice sample : none_found")
        
        return 0
        
    except Exception as exc:
        print(f"Inspection failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
