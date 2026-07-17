"""Generate and play a prebuilt Gemini TTS voice demo on Windows."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.speech.audio.artifacts import is_valid_wav
from beta.infrastructure.speech.playback.windows import WindowsAudioPlayer
from beta.infrastructure.speech.tts.google_vertex_gemini import (
    GoogleVertexGeminiTtsError,
    GoogleVertexGeminiTtsProvider,
)
from beta.interaction.voice.contracts import SpeechRequest

_PROJECT_ID = "datn-2251162143-287"
_LOCATION = "us-east4"
_MODEL = "gemini-2.5-flash-tts"
_DEFAULT_STYLE = "Giọng nữ trẻ trung, năng động, tinh nghịch, nói tiếng Việt tự nhiên."


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Beta Gemini TTS styled voice demo (not character voice cloning)."
    )
    parser.add_argument("--character", required=True, help="Character profile ID, for example mambo.")
    parser.add_argument("--text", required=True, help="Text to synthesize.")
    parser.add_argument("--style", default=_DEFAULT_STYLE, help="Gemini TTS delivery instruction.")
    parser.add_argument("--no-play", action="store_true", help="Generate WAV without Windows playback.")
    args = parser.parse_args()

    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.character):
        print("Invalid character profile ID.", file=sys.stderr)
        return 2
    if not (_PROJECT_ROOT / "profiles" / "characters" / args.character / "CHARACTER.md").is_file():
        print(f"Character profile not found: {args.character}", file=sys.stderr)
        return 2

    output_dir = _PROJECT_ROOT / "var" / "output" / "voice-demo"
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"{args.character}-{timestamp}.wav"
    provider = GoogleVertexGeminiTtsProvider(
        project=_PROJECT_ID,
        location=_LOCATION,
        model=_MODEL,
        style=args.style,
    )
    request = SpeechRequest(
        text=args.text,
        character_profile_id=args.character,
        language="vi-VN",
        output_path=output_path,
        play_audio=not args.no_play,
    )

    try:
        artifact = provider.synthesize(request)
    except (GoogleVertexGeminiTtsError, ValueError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1

    if not is_valid_wav(artifact.path):
        print(f"Demo failed: generated WAV is invalid: {artifact.path}", file=sys.stderr)
        return 1

    playback_result = "not_requested"
    if request.play_audio:
        if not WindowsAudioPlayer().play(artifact.path):
            print("Demo failed: Windows playback failed.", file=sys.stderr)
            return 1
        playback_result = "success"

    metadata = provider.last_response
    assert metadata is not None
    print("Beta Voice Demo")
    print(f"HTTP status       : {metadata.http_status}")
    print(f"Model             : {metadata.model}")
    print(f"MIME/audio format : {metadata.mime_type} -> WAV PCM16 mono {metadata.sample_rate_hz} Hz")
    print(f"Character profile : {args.character}")
    print("Voice label       : Gemini TTS styled voice; not a cloned or character-matched Mambo voice.")
    print(f"Output file       : {artifact.path}")
    print(f"File size         : {artifact.size_bytes} bytes")
    print(f"Playback          : {playback_result}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
