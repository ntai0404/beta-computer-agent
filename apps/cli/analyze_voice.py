"""
apps/cli/analyze_voice.py

CLI skeleton for voice reference analysis.

Usage:
  python apps/cli/analyze_voice.py --character-profile mambo --input path/to/ref.wav

Options:
  --character-profile  Profile ID (e.g. 'mambo')
  --input              Local path to audio or video file (NOT a URL)
  --provider           Multimodal provider to use (default: auto-detect)
  --model              Specific model name
  --output             Output path for voice-hint JSON
  --dry-run            Validate inputs but do not call any provider
  --overwrite          Allow overwriting existing analysis output

This CLI:
  - Does NOT download files from the Internet.
  - Does NOT accept URLs as input.
  - Does NOT produce fake results when provider is unavailable.
  - Does NOT identify or name the speaker.
  - Reports provider availability status clearly.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.llm.multimodal.voice_hint_analyzer import (
    VoiceHintAnalyzer,
    _detect_media_type,
    _sha256,
)

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


_SUPPORTED_EXTENSIONS = {
    ".wav", ".mp3", ".ogg", ".flac", ".m4a",
    ".mp4", ".webm", ".mkv", ".avi",
}

_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "var" / "artifacts" / "voice-analysis"


def _load_provider(provider_name: str | None, model_name: str | None):
    """
    Attempt to load a multimodal provider.

    Returns (provider, warnings). provider is None if not available.
    """
    warnings = []
    if provider_name is None:
        warnings.append(
            "No multimodal provider configured. "
            "Use --provider to specify one. "
            "Available: [none configured in this milestone]"
        )
        return None, warnings

    # Future: load provider from registry by name.
    warnings.append(
        f"Provider '{provider_name}' is not yet implemented. "
        "No analysis will be performed."
    )
    return None, warnings


def cmd_analyze(args: argparse.Namespace) -> int:
    # --- Validate input path (no URLs)
    input_path = Path(args.input)
    if str(args.input).startswith(("http://", "https://", "ftp://")):
        print("Error: --input must be a local file path, not a URL.", file=sys.stderr)
        return 2

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}", file=sys.stderr)
        return 2

    if not input_path.is_file():
        print(f"Error: Input path is not a file: {input_path}", file=sys.stderr)
        return 2

    if input_path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
        print(
            f"Error: Unsupported file type '{input_path.suffix}'. "
            f"Supported: {', '.join(sorted(_SUPPORTED_EXTENSIONS))}",
            file=sys.stderr,
        )
        return 2

    media_type = _detect_media_type(input_path)
    file_hash = _sha256(input_path)
    file_size = input_path.stat().st_size

    print(f"Reference     : {input_path}")
    print(f"Media type    : {media_type}")
    print(f"SHA-256       : {file_hash}")
    print(f"Size          : {file_size:,} bytes")
    print(f"Character     : {args.character_profile}")

    # --- Determine output path
    output_path = Path(args.output) if args.output else (
        _DEFAULT_OUTPUT_DIR / f"{args.character_profile}_voice_hint.json"
    )
    output_path = output_path.resolve()

    if output_path.exists() and not args.overwrite:
        print(
            f"Error: Output already exists: {output_path}. "
            "Use --overwrite to replace it.",
            file=sys.stderr,
        )
        return 2

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # --- Load provider
    provider, provider_warnings = _load_provider(
        getattr(args, "provider", None),
        getattr(args, "model", None),
    )

    for w in provider_warnings:
        print(f"Warning : {w}", file=sys.stderr)

    if args.dry_run:
        print("\n[dry-run] Validation complete. No provider called.")
        print(f"[dry-run] Output would be: {output_path}")
        return 0

    if provider is None:
        print(
            "\nStatus: PENDING ANALYSIS\n"
            "No multimodal provider is available or configured.\n"
            "Voice Hint has NOT been generated.\n"
            "Configure a multimodal provider via --provider and retry.",
            file=sys.stderr,
        )
        return 1

    # --- Run analysis (reached only when provider is available)
    analyzer = VoiceHintAnalyzer(provider=provider)
    try:
        hint = analyzer.analyze(
            reference_path=input_path,
            character_profile_id=args.character_profile,
            persona_alias=args.character_profile.capitalize(),
        )
    except Exception as exc:
        print(f"Analysis error: {exc}", file=sys.stderr)
        return 1

    # --- Serialize hint (simple dict for now)
    hint_dict = {
        "profile_id": hint.profile_id,
        "persona_alias": hint.persona_alias,
        "canonical_character_id": hint.canonical_character_id,
        "canonical_identity_status": hint.canonical_identity_status,
        "overall_confidence": hint.overall_confidence,
        "warnings": hint.warnings,
        "analysis_provider": hint.analysis_provider,
        "analysis_model": hint.analysis_model,
        "analyzed_at": hint.analyzed_at.isoformat() if hint.analyzed_at else None,
        "version": hint.version,
    }

    output_path.write_text(
        json.dumps(hint_dict, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nVoice Hint written: {output_path}")
    if hint.warnings:
        for w in hint.warnings:
            print(f"Warning : {w}", file=sys.stderr)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="analyze_voice",
        description=(
            "Beta Computer Agent — Voice Reference Analysis CLI\n\n"
            "Analyzes a local audio or video file to produce a Voice Hint.\n"
            "Does NOT download files. Does NOT identify speakers. "
            "Does NOT produce fake results."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--character-profile",
        required=True,
        metavar="PROFILE_ID",
        help="Character profile ID (e.g. 'mambo').",
    )
    parser.add_argument(
        "--input",
        required=True,
        metavar="LOCAL_PATH",
        help="Local path to audio or video file. NOT a URL.",
    )
    parser.add_argument(
        "--provider",
        default=None,
        metavar="PROVIDER",
        help="Multimodal analysis provider name. None currently available.",
    )
    parser.add_argument(
        "--model",
        default=None,
        metavar="MODEL",
        help="Specific model name for the provider.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Output JSON path. Default: var/artifacts/voice-analysis/<profile>_voice_hint.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs only. Do not call any provider.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow overwriting an existing analysis output.",
    )

    args = parser.parse_args()
    return cmd_analyze(args)


if __name__ == "__main__":
    sys.exit(main())
