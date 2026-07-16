"""Inspect the real I/O contracts for Beta voice pipelines."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.interaction.voice.contracts import PipelinePreference  # noqa: E402
from beta.interaction.voice.pipeline import VoicePipelineSelector  # noqa: E402
from beta.interaction.voice.resolver import VoiceProfileResolver  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Beta Computer Agent - Voice I/O inspector")
    parser.add_argument("--character-profile", default="mambo")
    args = parser.parse_args()

    resolver = VoiceProfileResolver(_PROJECT_ROOT)
    selector = VoicePipelineSelector()
    profile = resolver.resolve(args.character_profile)
    selector.select(profile, PipelinePreference.AUTO)

    print(f"Voice I/O for profile: {args.character_profile}")
    print(f"Current pipeline      : {profile.selected_pipeline.value}")
    print(f"Readiness             : {profile.readiness_status.value}")
    print(f"Output label          : Beta default system voice (not character matched)")
    print("")
    print("Voice Hint Analysis")
    print("  Input  : local audio/video reference + optional existing transcript + metadata")
    print("  Output : VoiceHint metadata JSON, warnings, confidence, source checksums")
    print("  Current: pending unless a configured provider and approved upload exist")
    print("")
    print("Base TTS")
    print("  Input  : text + provider-supported VoiceHint subset")
    print("  Output : source WAV audio")
    print("  Current: windows-system fallback only")
    print("")
    print("RVC Conversion")
    print("  Input  : source WAV audio + trusted RVC conversion model")
    print("  Output : converted WAV audio")
    print("  Current: discovery only; models are not loaded")
    print("")
    print("Final Voice Pipeline")
    print("  Input  : SpeechRequest(text, character_profile_id, pipeline_preference)")
    print("  Output : SpeechArtifact WAV + warnings + pipeline trace")
    print("  Current: not character matched unless a real provider/model is approved and run")
    if profile.warnings:
        print("")
        print("Warnings:")
        for warning in profile.warnings:
            print(f"  - {warning}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
