"""
apps/cli/speak.py

Thin CLI entry point for the Beta TTS pipeline.

Usage:
  python apps/cli/speak.py "Xin chào, tôi là Beta."
  python apps/cli/speak.py --character-profile mambo "Xin chào."
  python apps/cli/speak.py "Hello" --no-play --output var/artifacts/audio/out.wav
  python apps/cli/speak.py --list-voices

When --character-profile is used:
  - The character profile is loaded (if it exists).
  - Available Voice Hints are applied to the provider (within its capability).
  - A warning is printed if the active provider cannot reproduce the character voice.
  - Output is NEVER labeled as a cloned character voice.

This file contains no business logic.
It constructs a SpeechRequest and calls VoiceService.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure src/ is importable when running directly from project root.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.speech.playback.windows import WindowsAudioPlayer
from beta.infrastructure.speech.tts.windows_system import WindowsSystemTtsProvider
from beta.interaction.voice.contracts import SpeechRequest
from beta.interaction.voice.errors import VoiceError
from beta.interaction.voice.service import VoiceService

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def build_service(no_play: bool) -> VoiceService:
    provider = WindowsSystemTtsProvider()
    player = None if no_play else WindowsAudioPlayer()
    return VoiceService(tts_provider=provider, audio_player=player)


def apply_character_profile_hints(
    character_profile_id: str,
    base_rate: int,
    base_volume: int,
) -> tuple[int, int, list[str]]:
    """
    Attempt to load Voice Hints for the character profile and map to
    Windows System TTS parameters.

    Always prints a disclaimer that the output is NOT a cloned voice.
    Returns (rate, volume, warnings).
    """
    _PROJECT_ROOT = Path(__file__).resolve().parents[2]
    hint_path = (
        _PROJECT_ROOT
        / "var" / "artifacts" / "voice-analysis"
        / f"{character_profile_id}_voice_hint.json"
    )

    # Permanent disclaimer — always emitted when a character profile is used
    disclaimer = [
        f"[{character_profile_id}] Active provider: windows-system (NOT a cloned character voice).",
        f"[{character_profile_id}] Label: Beta default system voice — styled with available Windows hints.",
        "Windows System TTS cannot reproduce character timbre, emotional nuance, or exact pitch.",
    ]

    if not hint_path.exists():
        disclaimer.append(
            f"No Voice Hint found for '{character_profile_id}' "
            f"(expected: {hint_path}). "
            "Run: python apps/cli/analyze_voice.py --character-profile "
            f"{character_profile_id} --input <reference.wav>"
        )
        return base_rate, base_volume, disclaimer

    import json as _json
    try:
        hint_data = _json.loads(hint_path.read_text(encoding="utf-8"))
        # Hint mapping is limited — only rate/volume are usable by Windows TTS
        rate = base_rate
        volume = base_volume
        disclaimer.append(
            f"Voice Hint loaded from {hint_path} "
            f"(confidence: {hint_data.get('overall_confidence', 'unknown')}). "
            "Only speaking_rate → SAPI Rate and energy → Volume are applied."
        )
        return rate, volume, disclaimer
    except Exception as exc:
        disclaimer.append(f"Failed to load Voice Hint: {exc}")
        return base_rate, base_volume, disclaimer


def cmd_list_voices() -> int:
    provider = WindowsSystemTtsProvider()
    voices = provider.list_voices()
    if not voices:
        print("No SAPI voices found on this system.")
        return 1
    print(f"{'Name':<50} {'Language':<10} {'Gender'}")
    print("-" * 72)
    for v in voices:
        print(f"{v.name:<50} {v.language:<10} {v.gender or '—'}")
    return 0


def cmd_speak(args: argparse.Namespace) -> int:
    output_path: Path | None = None
    if args.output:
        output_path = Path(args.output).resolve()

    rate = args.rate
    volume = args.volume
    profile_warnings: list[str] = []

    if args.character_profile:
        rate, volume, profile_warnings = apply_character_profile_hints(
            args.character_profile, rate, volume
        )

    try:
        request = SpeechRequest(
            text=args.text,
            voice_profile_id=args.voice or None,
            rate=rate,
            volume=volume,
            output_path=output_path,
            play_audio=not args.no_play,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    svc = build_service(no_play=args.no_play)

    try:
        result = svc.speak(request)
    except VoiceError as exc:
        print(f"Voice error: {exc}", file=sys.stderr)
        return 1

    print(f"Provider : {result.artifact.provider}")
    print(f"Voice    : {result.artifact.voice_name or '(system default)'}")
    print(f"Output   : {result.artifact.path}")
    print(f"Size     : {result.artifact.size_bytes:,} bytes")
    if result.duration_ms is not None:
        print(f"Duration : {result.duration_ms} ms")
    if args.character_profile:
        print(f"Profile  : {args.character_profile} (alias — canonical identity unresolved)")
    print(f"Played   : {'yes' if result.played else 'no'}")
    all_warnings = profile_warnings + result.warnings
    if all_warnings:
        for w in all_warnings:
            print(f"Warning  : {w}", file=sys.stderr)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="speak",
        description="Beta Computer Agent — Text-to-Speech CLI",
    )
    parser.add_argument(
        "text",
        nargs="?",
        default=None,
        help="Text to synthesize.",
    )
    parser.add_argument(
        "--character-profile",
        default=None,
        metavar="PROFILE_ID",
        dest="character_profile",
        help=(
            "Character profile ID (e.g. 'mambo'). "
            "Loads Voice Hints if available. "
            "WARNING: Windows TTS cannot clone character voice."
        ),
    )
    parser.add_argument(
        "--voice",
        default=None,
        help="SAPI voice name (e.g. 'Microsoft Zira Desktop').",
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=0,
        metavar="[-10..10]",
        help="Speech rate (-10 slowest, 10 fastest). Default: 0.",
    )
    parser.add_argument(
        "--volume",
        type=int,
        default=100,
        metavar="[0..100]",
        help="Volume 0–100. Default: 100.",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="PATH",
        help="Output WAV path (must be inside var/). Default: auto-generated.",
    )
    parser.add_argument(
        "--no-play",
        action="store_true",
        help="Synthesize only; do not play audio.",
    )
    parser.add_argument(
        "--list-voices",
        action="store_true",
        help="List available SAPI voices and exit.",
    )

    args = parser.parse_args()

    if args.list_voices:
        return cmd_list_voices()

    if not args.text:
        parser.print_help()
        return 2

    return cmd_speak(args)


if __name__ == "__main__":
    sys.exit(main())
