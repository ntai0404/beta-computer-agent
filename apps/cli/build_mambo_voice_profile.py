"""Build the cached local-provenance profile for Mambo-inspired Gemini TTS."""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.speech.tts.styled_voice_profile import build_styled_voice_profile

_SAMPLES = (
    _PROJECT_ROOT
    / "var"
    / "sandbox"
    / "Desktop_Gremlin_tracen"
    / "Desktop_Gremlin"
    / "Sounds"
    / "Cafe"
    / "mambo.wav",
    _PROJECT_ROOT
    / "var"
    / "sandbox"
    / "Desktop_Gremlin_tracen"
    / "Desktop_Gremlin"
    / "Sounds"
    / "Doto"
    / "mambo.wav",
)


def main() -> int:
    profile_path = _PROJECT_ROOT / "profiles" / "characters" / "mambo" / "voice.yaml"
    try:
        profile, changed = build_styled_voice_profile(
            profile_path,
            sample_paths=list(_SAMPLES),
            base_voice="Kore",
            style_prompt=(
                "Deliver Vietnamese with a bright, youthful, lively, playful energy. "
                "Keep diction clear and friendly."
            ),
            analyzer_model="local-provenance-hash-only",
            label="mambo-inspired-gemini-tts",
            clone_status="not_cloned",
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"Profile build failed: {exc}", file=sys.stderr)
        return 1

    print(f"Profile path          : {profile_path}")
    print(f"Profile action        : {'rebuilt' if changed else 'cached_unchanged'}")
    print(f"Source sample hashes  : {len(profile.source_sample_hashes)}")
    print(f"Analyzer model        : {profile.analyzer_model}")
    print("Analyzer API calls    : 0")
    print(f"Label                 : {profile.label}")
    print(f"Clone status          : {profile.clone_status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
