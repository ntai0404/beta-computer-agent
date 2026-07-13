"""
apps/cli/list_voice_profiles.py

CLI to list available voice profiles and their pipeline readiness.
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
    parser = argparse.ArgumentParser(description="Beta Computer Agent — List Voice Profiles")
    parser.parse_args()

    resolver = VoiceProfileResolver(_PROJECT_ROOT)
    selector = VoicePipelineSelector()
    
    profiles_dir = _PROJECT_ROOT / "profiles" / "characters"
    if not profiles_dir.exists():
        print("No profiles directory found.")
        return 0
        
    print(f"{'Profile ID':<20} | {'Alias':<15} | {'Identity':<15} | {'Readiness':<20} | {'Pipeline':<25}")
    print("-" * 105)
    
    for char_dir in profiles_dir.iterdir():
        if char_dir.is_dir() and (char_dir / "CHARACTER.md").exists():
            profile_id = char_dir.name
            try:
                profile = resolver.resolve(profile_id)
                selector.select(profile, PipelinePreference.AUTO)
                
                print(f"{profile_id:<20} | {profile.persona_alias:<15} | {profile.canonical_identity_status:<15} | {profile.readiness_status.value:<20} | {profile.selected_pipeline.value:<25}")
            except Exception as e:
                print(f"{profile_id:<20} | ERROR: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
