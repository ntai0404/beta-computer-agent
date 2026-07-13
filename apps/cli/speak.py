"""
apps/cli/speak.py

CLI to synthesize text to speech using the Beta Voice Engine.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.speech.conversion.rvc.discovery import RvcConversionProvider
from beta.infrastructure.speech.playback.windows import WindowsAudioPlayer
from beta.infrastructure.speech.tts.windows_system import WindowsSystemTtsProvider
from beta.interaction.voice.contracts import PipelinePreference, SpeechRequest, VoiceHint
from beta.interaction.voice.pipeline import VoicePipelineSelector
from beta.interaction.voice.resolver import VoiceProfileResolver
from beta.interaction.voice.service import VoiceService

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def main() -> int:
    parser = argparse.ArgumentParser(description="Beta Computer Agent — Speak CLI")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("--character-profile", required=True, help="Character profile ID (e.g., 'mambo')")
    parser.add_argument("--pipeline", default="auto", choices=[p.value for p in PipelinePreference], help="Pipeline preference")
    parser.add_argument("--rate", type=float, default=1.0, help="Speaking rate (1.0 is default)")
    parser.add_argument("--volume", type=float, default=1.0, help="Volume (1.0 is default)")
    parser.add_argument("--output", type=Path, help="Output WAV path (optional)")
    parser.add_argument("--no-play", action="store_true", help="Do not play audio, just generate")
    parser.add_argument("--allow-untrusted-model", action="store_true", help="Allow using untrusted models (Blocked in this milestone)")
    
    args = parser.parse_args()

    artifacts_dir = _PROJECT_ROOT / "var" / "artifacts"
    
    resolver = VoiceProfileResolver(_PROJECT_ROOT)
    selector = VoicePipelineSelector()
    
    tts_providers = {"windows-system": WindowsSystemTtsProvider()}
    conv_providers = {"rvc": RvcConversionProvider()}
    audio_player = WindowsAudioPlayer()
    
    service = VoiceService(
        resolver=resolver,
        pipeline_selector=selector,
        tts_providers=tts_providers,
        conversion_providers=conv_providers,
        audio_player=audio_player,
        artifacts_dir=artifacts_dir
    )
    
    request = SpeechRequest(
        text=args.text,
        character_profile_id=args.character_profile,
        rate=args.rate,
        volume=args.volume,
        play_audio=not args.no_play,
        output_path=args.output,
        pipeline_preference=PipelinePreference(args.pipeline),
        allow_untrusted_model=args.allow_untrusted_model
    )
    
    try:
        result = service.speak(request)
        print("\n--- Speech Result ---")
        print(f"Artifact: {result.final_artifact.path if result.final_artifact else 'None'}")
        print(f"Provider: {result.final_artifact.provider if result.final_artifact else 'None'}")
        print("Trace:")
        for t in result.pipeline_trace:
            print(f"  -> {t}")
        if result.warnings:
            print("\nWarnings:")
            for w in result.warnings:
                print(f"  [!] {w}")
        return 0
    except Exception as e:
        print(f"\nFailed to speak: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
