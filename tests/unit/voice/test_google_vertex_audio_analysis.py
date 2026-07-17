import base64
import io
import json
import wave
from pathlib import Path

import beta.infrastructure.speech.tts.google_vertex_audio_analysis as audio_analysis
import beta.infrastructure.speech.tts.google_vertex_gemini as gemini_tts


def _write_wav(path: Path, frames: bytes) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24_000)
        wav_file.writeframes(frames)


def test_audio_analysis_merges_two_wavs_and_sanitizes_structured_response(tmp_path: Path):
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    _write_wav(first, b"\x01\x00" * 4)
    _write_wav(second, b"\x02\x00" * 4)
    merged = audio_analysis._merge_wav_samples([first, second])
    with wave.open(io.BytesIO(merged), "rb") as wav_file:
        assert wav_file.getframerate() == 24_000
        assert wav_file.getnframes() == 4 + 6_000 + 4

    raw = {
        "pitch": "high",
        "timbre": "light",
        "pace": "fast",
        "rhythm": "fragmented",
        "energy": "high",
        "articulation": "short vowels",
        "expressiveness": "high",
        "pronunciation_accent_notes": "no clear words",
        "generated_style_prompt": "Use a bright, fast delivery.",
        "confidence": 1.5,
        "limitations": ["short sample"],
        "speaker_identity": "must be dropped",
    }
    sanitized = audio_analysis._sanitize_analysis(raw)

    assert sanitized["confidence"] == 1.0
    assert "speaker_identity" not in sanitized


def test_audio_analyzer_sends_one_audio_part_and_returns_structured_result(tmp_path: Path):
    first = tmp_path / "first.wav"
    second = tmp_path / "second.wav"
    _write_wav(first, b"\x00\x00" * 4)
    _write_wav(second, b"\x00\x00" * 4)
    analysis = {
        "pitch": "high",
        "timbre": "light",
        "pace": "fast",
        "rhythm": "irregular",
        "energy": "high",
        "articulation": "short",
        "expressiveness": "strong",
        "pronunciation_accent_notes": "none",
        "generated_style_prompt": "Use lively delivery.",
        "confidence": 0.8,
        "limitations": ["short"],
    }

    class FakeClient:
        def __init__(self):
            self.calls = []

        def post_json(self, *args):
            self.calls.append(args)
            return gemini_tts._HttpResponse(
                200,
                {
                    "modelVersion": "gemini-2.5-flash-test",
                    "candidates": [{"content": {"parts": [{"text": json.dumps(analysis)}]}}],
                },
            )

    analyzer = audio_analysis.GoogleVertexAudioAnalyzer(
        project="project-a",
        location="us-east4",
    )
    fake = FakeClient()
    analyzer._client = fake

    result = analyzer.analyze_wav_samples([first, second])

    assert result.api_call_count == 1
    assert result.model_version == "gemini-2.5-flash-test"
    assert result.analysis["generated_style_prompt"] == "Use lively delivery."
    request_payload = fake.calls[0][2]
    audio_part = request_payload["contents"]["parts"][1]["inline_data"]
    assert audio_part["mime_type"] == "audio/wav"
    assert base64.b64decode(audio_part["data"])
    assert "Do not identify" in request_payload["contents"]["parts"][0]["text"]
