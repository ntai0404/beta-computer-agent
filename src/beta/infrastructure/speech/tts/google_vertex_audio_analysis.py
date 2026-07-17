"""One-call Vertex Gemini audio analysis for an explicitly approved profile build."""

from __future__ import annotations

import base64
import io
import json
import time
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beta.infrastructure.speech.tts.google_vertex_gemini import (
    GoogleVertexGeminiTtsError,
    _VertexAdcClient,
)


@dataclass(frozen=True)
class AudioAnalysisResult:
    analysis: dict[str, Any]
    model: str
    model_version: str
    endpoint: str
    api_call_count: int


class GoogleVertexAudioAnalyzer:
    """Analyzes acoustic traits only and explicitly forbids identity inference."""

    def __init__(self, *, project: str, location: str, model: str = "gemini-2.5-flash") -> None:
        self.project = project
        self.location = location
        self.model = model
        self._client = _VertexAdcClient()

    def analyze_wav_samples(self, sample_paths: list[Path]) -> AudioAnalysisResult:
        merged_wav = _merge_wav_samples(sample_paths)
        request = {
            "contents": {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Analyze only observable acoustic delivery in this merged reference audio. "
                            "Do not identify, guess, compare, or name any speaker, character, person, or identity. "
                            "Return concise JSON for pitch, timbre, pace, rhythm, energy, articulation, "
                            "expressiveness, pronunciation_accent_notes, confidence, limitations, and "
                            "generated_style_prompt. The style prompt must describe delivery only and must not "
                            "claim voice matching or cloning."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "audio/wav",
                            "data": base64.b64encode(merged_wav).decode("ascii"),
                        }
                    },
                ],
            },
            "generation_config": {
                "response_mime_type": "application/json",
                "response_schema": _analysis_schema(),
                "temperature": 0.2,
            },
        }
        started = time.monotonic()
        response = self._client.post_json(self.endpoint, self.project, request, started)
        if response.status_code != 200:
            raise GoogleVertexGeminiTtsError(
                "Vertex audio analysis failed: "
                f"http={response.status_code}; status={response.error_status or 'unknown'}; "
                f"model={self.model}; location={self.location}; "
                f"message={response.error_message or 'none'}"
            )
        analysis = _sanitize_analysis(_extract_text_json(response.payload))
        return AudioAnalysisResult(
            analysis=analysis,
            model=self.model,
            model_version=str(response.payload.get("modelVersion") or self.model),
            endpoint=self.endpoint,
            api_call_count=1,
        )

    @property
    def endpoint(self) -> str:
        host = "aiplatform.googleapis.com" if self.location == "global" else f"{self.location}-aiplatform.googleapis.com"
        return (
            f"https://{host}/v1beta1/projects/{self.project}/locations/{self.location}"
            f"/publishers/google/models/{self.model}:generateContent"
        )


def _merge_wav_samples(sample_paths: list[Path]) -> bytes:
    if len(sample_paths) != 2:
        raise ValueError("Exactly two WAV samples are required for the Mambo profile build.")
    parameters: tuple[int, int, int] | None = None
    frames: list[bytes] = []
    for sample_path in sample_paths:
        with wave.open(str(sample_path), "rb") as wav_file:
            current = (wav_file.getnchannels(), wav_file.getsampwidth(), wav_file.getframerate())
            if parameters is None:
                parameters = current
            elif current != parameters:
                raise ValueError("Reference WAV formats differ; cannot build a single audio analysis request.")
            frames.append(wav_file.readframes(wav_file.getnframes()))
    assert parameters is not None
    channels, sample_width, sample_rate = parameters
    silence = b"\x00" * int(sample_rate * 0.25) * channels * sample_width
    merged = io.BytesIO()
    with wave.open(merged, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(silence.join(frames))
    return merged.getvalue()


def _analysis_schema() -> dict[str, Any]:
    text_fields = (
        "pitch",
        "timbre",
        "pace",
        "rhythm",
        "energy",
        "articulation",
        "expressiveness",
        "pronunciation_accent_notes",
        "generated_style_prompt",
    )
    properties: dict[str, Any] = {name: {"type": "STRING"} for name in text_fields}
    properties["confidence"] = {"type": "NUMBER"}
    properties["limitations"] = {"type": "ARRAY", "items": {"type": "STRING"}}
    return {"type": "OBJECT", "properties": properties, "required": [*text_fields, "confidence", "limitations"]}


def _extract_text_json(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("candidates", [])
    if not candidates:
        raise GoogleVertexGeminiTtsError("Vertex audio analysis response had no candidates.")
    parts = candidates[0].get("content", {}).get("parts", [])
    if not isinstance(parts, list):
        parts = [parts]
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            try:
                value = json.loads(part["text"])
            except json.JSONDecodeError as exc:
                raise GoogleVertexGeminiTtsError("Vertex audio analysis did not return JSON.") from exc
            if isinstance(value, dict):
                return value
    raise GoogleVertexGeminiTtsError("Vertex audio analysis response had no JSON text.")


def _sanitize_analysis(raw: dict[str, Any]) -> dict[str, Any]:
    text_fields = (
        "pitch",
        "timbre",
        "pace",
        "rhythm",
        "energy",
        "articulation",
        "expressiveness",
        "pronunciation_accent_notes",
        "generated_style_prompt",
    )
    missing = [field for field in text_fields if not isinstance(raw.get(field), str) or not raw[field].strip()]
    if missing:
        raise GoogleVertexGeminiTtsError(f"Vertex audio analysis missing fields: {', '.join(missing)}")
    limitations = raw.get("limitations")
    if not isinstance(limitations, list) or not all(isinstance(item, str) for item in limitations):
        raise GoogleVertexGeminiTtsError("Vertex audio analysis limitations are invalid.")
    try:
        confidence = float(raw.get("confidence"))
    except (TypeError, ValueError) as exc:
        raise GoogleVertexGeminiTtsError("Vertex audio analysis confidence is invalid.") from exc
    return {
        **{field: raw[field].strip() for field in text_fields},
        "confidence": max(0.0, min(1.0, confidence)),
        "limitations": [item.strip() for item in limitations if item.strip()],
    }
