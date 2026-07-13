"""
apps/cli/inspect_voice_pipeline.py

CLI to inspect the voice pipeline resolution for a given character profile.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.interaction.voice.contracts import PipelinePreference
from beta.interaction.voice.pipeline import VoicePipelineSelector
from beta.interaction.voice.resolver import VoiceProfileResolver


def main() -> int:
    parser = argparse.ArgumentParser(description="Beta Computer Agent — Voice Pipeline Inspector")
    parser.add_argument("--character-profile", required=True, help="Character profile ID (e.g., 'mambo')")
    args = parser.parse_args()

    resolver = VoiceProfileResolver(_PROJECT_ROOT)
    selector = VoicePipelineSelector()
    
    try:
        profile = resolver.resolve(args.character_profile)
        selector.select(profile, PipelinePreference.AUTO)
        
        print(f"--- Voice Pipeline Inspection for '{args.character_profile}' ---")
        print(f"Alias: {profile.persona_alias}")
        print(f"Canonical Identity Status: {profile.canonical_identity_status}")
        print(f"Readiness Status: {profile.readiness_status.value}")
        print(f"\nSelected Pipeline: {profile.selected_pipeline.value}")
        print(f"  TTS Provider: {profile.selected_tts_provider}")
        print(f"  Conversion Provider: {profile.selected_conversion_provider or 'None'}")
        print(f"  Voice Name: {profile.selected_voice_name or 'Default'}")
        
        print("\nDiscovered Models:")
        if not profile.model_paths:
            print("  None")
        else:
            for k, v in profile.model_paths.items():
                print(f"  {k}: {v}")
                
        if profile.warnings:
            print("\nWarnings:")
            for w in profile.warnings:
                print(f"  [!] {w}")
                
        return 0
    except Exception as e:
        print(f"Failed to inspect pipeline: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
