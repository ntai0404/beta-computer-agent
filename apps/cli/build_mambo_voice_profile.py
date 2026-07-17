"""Build the cached local-provenance profile for Mambo-inspired Gemini TTS."""

from __future__ import annotations

import argparse
import json
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.character_assets.validation.security import compute_sha256
from beta.infrastructure.speech.tts.google_vertex_audio_analysis import GoogleVertexAudioAnalyzer
from beta.infrastructure.speech.tts.google_vertex_gemini import GoogleVertexGeminiTtsError
from beta.infrastructure.speech.tts.styled_voice_profile import (
    build_styled_voice_profile,
    load_styled_voice_profile,
)

_PROJECT_ID = "datn-2251162143-287"
_LOCATION = "us-east4"
_ANALYZER_MODEL = "gemini-2.5-flash"

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
    parser = argparse.ArgumentParser(
        description="Build a sample-informed, not-cloned Mambo-inspired Gemini TTS profile."
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Upload the merged local WAV references once for Vertex acoustic analysis.",
    )
    args = parser.parse_args()
    profile_path = _PROJECT_ROOT / "profiles" / "characters" / "mambo" / "voice.yaml"
    analysis_path = profile_path.with_name("voice-analysis.json")
    try:
        sample_evidence = _sample_evidence(_SAMPLES)
        hashes = tuple(item["sha256"] for item in sample_evidence)
        existing = load_styled_voice_profile(profile_path) if profile_path.exists() else None
        cache_valid = (
            existing is not None
            and existing.source_sample_hashes == hashes
            and existing.profile_generated_from_reference_audio
            and analysis_path.is_file()
        )
        if cache_valid and not args.rebuild:
            _print_profile(existing, profile_path, sample_evidence, "cached_unchanged", 0)
            return 0

        analysis_result = GoogleVertexAudioAnalyzer(
            project=_PROJECT_ID,
            location=_LOCATION,
            model=_ANALYZER_MODEL,
        ).analyze_wav_samples(list(_SAMPLES))
        sanitized_analysis = {
            "analyzer_source": "google_audio_analysis",
            "analyzer_model": analysis_result.model,
            "analyzer_model_version": analysis_result.model_version,
            "analyzer_endpoint": analysis_result.endpoint,
            "source_samples": sample_evidence,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "raw_sanitized_analysis": analysis_result.analysis,
        }
        analysis_path.write_text(
            json.dumps(sanitized_analysis, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )
        profile, changed = build_styled_voice_profile(
            profile_path,
            sample_paths=list(_SAMPLES),
            base_voice="Kore",
            style_prompt=analysis_result.analysis["generated_style_prompt"],
            analyzer_model=analysis_result.model,
            label="mambo-inspired-gemini-tts",
            clone_status="not_cloned",
            analyzer_source="google_audio_analysis",
            analyzer_model_version=analysis_result.model_version,
            analysis_path=analysis_path.name,
            profile_generated_from_reference_audio=True,
            force_rebuild=True,
        )
    except (FileNotFoundError, GoogleVertexGeminiTtsError, ValueError) as exc:
        print(f"Profile build failed: {exc}", file=sys.stderr)
        return 1

    _print_profile(
        profile,
        profile_path,
        sample_evidence,
        "rebuilt" if changed else "cached_unchanged",
        analysis_result.api_call_count,
    )
    print(f"Analyzer endpoint     : {analysis_result.endpoint}")
    print(f"Analysis output       : {analysis_path}")
    print("Raw analysis          : saved as sanitized JSON")
    return 0


def _sample_evidence(sample_paths: tuple[Path, ...]) -> list[dict[str, object]]:
    evidence: list[dict[str, object]] = []
    for path in sample_paths:
        with wave.open(str(path), "rb") as wav_file:
            duration_ms = round(wav_file.getnframes() / wav_file.getframerate() * 1_000)
        evidence.append(
            {
                "path": str(path.relative_to(_PROJECT_ROOT)),
                "duration_ms": duration_ms,
                "sha256": compute_sha256(path),
            }
        )
    return evidence


def _print_profile(profile, profile_path: Path, samples: list[dict[str, object]], action: str, calls: int) -> None:
    print(f"Profile path                         : {profile_path}")
    print(f"Profile action                       : {action}")
    for index, sample in enumerate(samples, start=1):
        print(f"Reference {index} path                 : {sample['path']}")
        print(f"Reference {index} duration_ms          : {sample['duration_ms']}")
        print(f"Reference {index} sha256               : {sample['sha256']}")
    print(f"Analyzer source                       : {profile.analyzer_source}")
    print(f"Analyzer model                        : {profile.analyzer_model}")
    print(f"Analyzer model version                : {profile.analyzer_model_version}")
    print(f"Analyzer API calls                    : {calls}")
    print(f"Profile from reference audio          : {str(profile.profile_generated_from_reference_audio).lower()}")
    print(f"Generated style_prompt                : {profile.style_prompt}")
    print(f"Label                                 : {profile.label}")
    print(f"Clone status                          : {profile.clone_status}")


if __name__ == "__main__":
    sys.exit(main())
