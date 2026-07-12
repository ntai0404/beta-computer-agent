"""
apps/cli/speak.py

Thin CLI entry point for the Beta TTS pipeline.

Usage:
  python apps/cli/speak.py "Xin chào, tôi là Beta."
  python apps/cli/speak.py "Hello" --no-play --output var/artifacts/audio/out.wav
  python apps/cli/speak.py --list-voices

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

    try:
        request = SpeechRequest(
            text=args.text,
            voice_profile_id=args.voice or None,
            rate=args.rate,
            volume=args.volume,
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
    print(f"Played   : {'yes' if result.played else 'no'}")
    if result.warnings:
        for w in result.warnings:
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
