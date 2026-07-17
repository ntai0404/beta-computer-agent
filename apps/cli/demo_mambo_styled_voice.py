"""One-call Mambo-inspired Gemini TTS demo and latency benchmark."""

from __future__ import annotations

import argparse
import datetime as dt
import math
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.speech.audio.artifacts import is_valid_wav, wav_duration_ms
from beta.infrastructure.speech.playback.windows import WindowsAudioPlayer
from beta.infrastructure.speech.tts.google_vertex_gemini import (
    GoogleVertexGeminiTtsError,
    GoogleVertexGeminiTtsProvider,
)
from beta.infrastructure.speech.tts.styled_voice_profile import load_styled_voice_profile
from beta.interaction.voice.contracts import SpeechRequest

_PROJECT_ID = "datn-2251162143-287"
_LOCATION = "us-east4"
_MODEL = "gemini-2.5-flash-tts"


@dataclass(frozen=True)
class DemoRun:
    profile_load_ms: float
    prompt_build_ms: float
    auth_ms: float
    request_start_ms: float
    response_complete_ms: float
    wav_write_ms: float
    playback_start_ms: float | None
    total_to_playback_ms: float | None
    api_call_count: int
    input_text_length: int
    estimated_input_tokens: int
    output_duration_ms: int
    estimated_output_audio_tokens: float
    estimated_request_cost_usd: float
    http_status: int
    output_path: Path
    file_size: int
    playback_result: str
    mime_type: str


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Mambo-inspired Gemini TTS. This is styled prebuilt TTS, not a cloned voice."
    )
    parser.add_argument("--text", required=True, help="Vietnamese text to synthesize.")
    parser.add_argument("--emotion", default="neutral", choices=("neutral", "cheerful", "calm", "excited"))
    parser.add_argument("--benchmark-runs", type=int, default=0, help="Run a warm-up and N measured runs.")
    parser.add_argument("--no-play", action="store_true", help="Generate WAV without Windows playback.")
    args = parser.parse_args()
    if args.benchmark_runs < 0:
        parser.error("--benchmark-runs must be zero or greater.")

    try:
        if args.benchmark_runs:
            _run_benchmark(args.text, args.emotion, args.benchmark_runs, not args.no_play)
        else:
            _print_run("demo", _run_once(args.text, args.emotion, not args.no_play, "demo"))
    except (FileNotFoundError, GoogleVertexGeminiTtsError, ValueError) as exc:
        print(f"Demo failed: {exc}", file=sys.stderr)
        return 1
    return 0


def _run_benchmark(text: str, emotion: str, runs: int, play_audio: bool) -> None:
    warmup = _run_once(text, emotion, play_audio, "warmup")
    _print_run("warmup_not_counted", warmup)
    measurements = [
        _run_once(text, emotion, play_audio, f"run-{index}")
        for index in range(1, runs + 1)
    ]
    for index, result in enumerate(measurements, start=1):
        _print_run(f"benchmark_run_{index}", result)

    latencies = sorted(result.total_to_playback_ms or 0.0 for result in measurements)
    costs = [result.estimated_request_cost_usd for result in measurements]
    durations = [result.output_duration_ms for result in measurements]
    p95_index = max(0, math.ceil(len(latencies) * 0.95) - 1)
    print("Benchmark summary")
    print(f"runs                         : {runs}")
    print(f"measured Gemini API calls    : {sum(result.api_call_count for result in measurements)}")
    print(f"total Gemini API calls        : {warmup.api_call_count + sum(result.api_call_count for result in measurements)}")
    print(f"latency_min_ms                : {latencies[0]:.2f}")
    print(f"latency_median_ms             : {statistics.median(latencies):.2f}")
    print(f"latency_p95_ms                : {latencies[p95_index]:.2f}")
    print(f"latency_max_ms                : {latencies[-1]:.2f}")
    print(f"latency_average_ms            : {statistics.mean(latencies):.2f}")
    print(f"audio_duration_ms_per_run     : {durations}")
    print(f"estimated_cost_usd_per_run    : {[round(cost, 8) for cost in costs]}")
    print("cost_note                     : estimate from supplied token-rate formula, not billing export")


def _run_once(text: str, emotion: str, play_audio: bool, run_name: str) -> DemoRun:
    started = time.monotonic()
    profile_started = time.monotonic()
    profile = load_styled_voice_profile(
        _PROJECT_ROOT / "profiles" / "characters" / "mambo" / "voice.yaml"
    )
    profile_load_ms = (time.monotonic() - profile_started) * 1_000
    if profile.label != "mambo-inspired-gemini-tts" or profile.clone_status != "not_cloned":
        raise ValueError("Mambo profile must be labeled mambo-inspired-gemini-tts and not_cloned.")

    style = f"{profile.style_prompt} Emotion: {emotion}."
    output_dir = _PROJECT_ROOT / "var" / "output" / "voice-demo"
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output_path = output_dir / f"mambo-styled-{run_name}-{timestamp}.wav"
    provider = GoogleVertexGeminiTtsProvider(
        project=_PROJECT_ID,
        location=_LOCATION,
        model=_MODEL,
        style=style,
        voice_name=profile.base_voice,
    )
    artifact = provider.synthesize(
        SpeechRequest(
            text=text,
            character_profile_id="mambo",
            language="vi-VN",
            output_path=output_path,
            play_audio=play_audio,
        )
    )
    if not is_valid_wav(artifact.path):
        raise ValueError(f"Generated invalid WAV: {artifact.path}")
    metadata = provider.last_response
    assert metadata is not None
    duration_ms = wav_duration_ms(artifact.path)
    if duration_ms is None:
        raise ValueError(f"Cannot read generated WAV duration: {artifact.path}")

    playback_start_ms: float | None = None
    total_to_playback_ms: float | None = None
    playback_result = "not_requested"
    if play_audio:
        playback_start_ms = (time.monotonic() - started) * 1_000
        total_to_playback_ms = playback_start_ms
        if not WindowsAudioPlayer().play(artifact.path):
            raise ValueError("Windows playback failed.")
        playback_result = "success"

    estimated_input_tokens = max(1, math.ceil(metadata.prompt_characters / 4))
    estimated_output_audio_tokens = duration_ms / 1_000 * 25
    estimated_cost_usd = (
        estimated_input_tokens * 0.50 / 1_000_000
        + estimated_output_audio_tokens * 10 / 1_000_000
    )
    return DemoRun(
        profile_load_ms=profile_load_ms,
        prompt_build_ms=metadata.prompt_build_ms,
        auth_ms=metadata.auth_ms,
        request_start_ms=metadata.request_start_ms,
        response_complete_ms=metadata.response_complete_ms,
        wav_write_ms=metadata.wav_write_ms,
        playback_start_ms=playback_start_ms,
        total_to_playback_ms=total_to_playback_ms,
        api_call_count=metadata.api_call_count,
        input_text_length=len(text),
        estimated_input_tokens=estimated_input_tokens,
        output_duration_ms=duration_ms,
        estimated_output_audio_tokens=estimated_output_audio_tokens,
        estimated_request_cost_usd=estimated_cost_usd,
        http_status=metadata.http_status,
        output_path=artifact.path,
        file_size=artifact.size_bytes,
        playback_result=playback_result,
        mime_type=metadata.mime_type,
    )


def _print_run(name: str, result: DemoRun) -> None:
    print(f"Run: {name}")
    print(f"profile_load_ms                 : {result.profile_load_ms:.2f}")
    print(f"prompt_build_ms                 : {result.prompt_build_ms:.2f}")
    print(f"auth_ms                         : {result.auth_ms:.2f}")
    print(f"request_start_ms                : {result.request_start_ms:.2f}")
    print("first_audio_ms                  : not_available_unary")
    print(f"response_complete_ms            : {result.response_complete_ms:.2f}")
    print(f"wav_write_ms                    : {result.wav_write_ms:.2f}")
    print(
        "playback_start_ms               : "
        f"{result.playback_start_ms:.2f}" if result.playback_start_ms is not None else "playback_start_ms               : not_requested"
    )
    print(
        "total_to_playback_ms            : "
        f"{result.total_to_playback_ms:.2f}" if result.total_to_playback_ms is not None else "total_to_playback_ms            : not_requested"
    )
    print(f"API call count                  : {result.api_call_count}")
    print(f"input text length               : {result.input_text_length}")
    print(f"estimated input tokens          : {result.estimated_input_tokens}")
    print(f"output duration_ms              : {result.output_duration_ms}")
    print(f"estimated output audio tokens   : {result.estimated_output_audio_tokens:.2f}")
    print(f"estimated request_cost_usd      : {result.estimated_request_cost_usd:.8f}")
    print("cost note                       : estimate from supplied token-rate formula, not billing export")
    print(f"HTTP status                     : {result.http_status}")
    print(f"MIME/audio format               : {result.mime_type} -> WAV PCM16")
    print("voice label                     : mambo-inspired-gemini-tts; not cloned")
    print(f"output file                     : {result.output_path}")
    print(f"file size                       : {result.file_size} bytes")
    print(f"playback result                 : {result.playback_result}")
    print("transport                       : unary generateContent; streaming not implemented in this REST demo")


if __name__ == "__main__":
    sys.exit(main())
