"""Vertex AI Gemini TTS provider using Application Default Credentials."""

from __future__ import annotations

import base64
import datetime as dt
import json
import re
import urllib.error
import urllib.request
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from beta.infrastructure.character_assets.validation.security import compute_sha256
from beta.infrastructure.speech.tts.base import TtsProvider, VoiceInfo
from beta.interaction.voice.contracts import SpeechArtifact, SpeechRequest


class GoogleVertexGeminiTtsError(RuntimeError):
    """A sanitized error returned while calling Vertex AI Gemini TTS."""


@dataclass(frozen=True)
class GeminiTtsResponseMetadata:
    http_status: int
    model: str
    mime_type: str
    sample_rate_hz: int


@dataclass(frozen=True)
class _HttpResponse:
    status_code: int
    payload: dict[str, Any]
    error_status: str | None = None
    error_message: str | None = None


class GoogleVertexGeminiTtsProvider(TtsProvider):
    """Synthesizes prebuilt Gemini TTS voices; it does not clone a character voice."""

    def __init__(
        self,
        *,
        project: str,
        location: str,
        model: str,
        style: str,
        voice_name: str = "Kore",
    ) -> None:
        self.project = project
        self.location = location
        self.model = model
        self.style = style.strip()
        self.voice_name = voice_name
        self.last_response: GeminiTtsResponseMetadata | None = None

    @property
    def provider_id(self) -> str:
        return "google-vertex-gemini-tts"

    def synthesize(self, request: SpeechRequest) -> SpeechArtifact:
        if not request.text.strip():
            raise ValueError("Text must not be empty.")
        if request.output_path is None:
            raise ValueError("GoogleVertexGeminiTtsProvider requires an output path.")

        response = _authenticated_json_post(
            self._endpoint(),
            self.project,
            self._request_body(request),
        )
        if response.status_code != 200:
            raise GoogleVertexGeminiTtsError(
                _sanitized_error_message(response, self.model, self.location)
            )

        audio_bytes, mime_type = _extract_audio(response.payload)
        sample_rate_hz = _sample_rate_from_mime_type(mime_type)
        output_path = request.output_path
        _write_pcm16_wav(output_path, audio_bytes, sample_rate_hz)

        self.last_response = GeminiTtsResponseMetadata(
            http_status=response.status_code,
            model=self.model,
            mime_type=mime_type,
            sample_rate_hz=sample_rate_hz,
        )
        return SpeechArtifact(
            path=output_path,
            format="wav",
            sample_rate=sample_rate_hz,
            channels=1,
            provider=self.provider_id,
            pipeline="google_vertex_gemini_tts",
            character_profile_id=request.character_profile_id,
            generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
            size_bytes=output_path.stat().st_size,
            checksum=compute_sha256(output_path),
            provenance=(
                f"Vertex AI {self.model} prebuilt Gemini TTS voice '{self.voice_name}' "
                f"at {self.location}"
            ),
            warnings=[
                "Gemini TTS styled voice only; not a cloned or character-matched Mambo voice."
            ],
        )

    def list_voices(self) -> list[VoiceInfo]:
        return [
            VoiceInfo(
                name=self.voice_name,
                language="vi-VN",
                description="Configured prebuilt Gemini TTS voice.",
            )
        ]

    def health_check(self) -> None:
        if not self.project or not self.location or not self.model:
            raise GoogleVertexGeminiTtsError("Project, location, and model are required.")

    def _endpoint(self) -> str:
        host = (
            "aiplatform.googleapis.com"
            if self.location == "global"
            else f"{self.location}-aiplatform.googleapis.com"
        )
        return (
            f"https://{host}/v1beta1/projects/{self.project}/locations/{self.location}"
            f"/publishers/google/models/{self.model}:generateContent"
        )

    def _request_body(self, request: SpeechRequest) -> dict[str, Any]:
        style = self.style or "Speak naturally and clearly."
        prompt = f"{style}\n\nSpeak this text naturally in Vietnamese:\n{request.text}"
        return {
            "contents": {"role": "user", "parts": {"text": prompt}},
            "generation_config": {
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "language_code": request.language,
                    "voice_config": {
                        "prebuilt_voice_config": {"voice_name": self.voice_name}
                    },
                },
            },
        }


def _authenticated_json_post(
    url: str,
    project: str,
    payload: dict[str, Any],
) -> _HttpResponse:
    """POST with ADC while never exposing an access token in exceptions or output."""
    try:
        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(google.auth.transport.requests.Request())
    except Exception as exc:  # pragma: no cover - depends on local ADC configuration
        raise GoogleVertexGeminiTtsError(
            f"ADC unavailable: {type(exc).__name__}"
        ) from None

    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    request.add_header("Authorization", f"Bearer {credentials.token}")
    request.add_header("Content-Type", "application/json")
    request.add_header("x-goog-user-project", project)
    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return _HttpResponse(response.status, _read_json(response.read()))
    except urllib.error.HTTPError as exc:
        body = _read_json(exc.read())
        error = body.get("error", {})
        return _HttpResponse(
            exc.code,
            body,
            str(error.get("status") or "HTTP_ERROR"),
            str(error.get("message") or "")[:300],
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        raise GoogleVertexGeminiTtsError(
            f"Vertex request unavailable: {type(exc).__name__}"
        ) from None


def _read_json(raw: bytes) -> dict[str, Any]:
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return decoded if isinstance(decoded, dict) else {}


def _extract_audio(payload: dict[str, Any]) -> tuple[bytes, str]:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise GoogleVertexGeminiTtsError("Vertex response did not contain an audio candidate.")
    content = candidates[0].get("content", {})
    parts = content.get("parts", [])
    if not isinstance(parts, list):
        parts = [parts]
    for part in parts:
        if not isinstance(part, dict):
            continue
        inline_data = part.get("inlineData") or part.get("inline_data")
        if not isinstance(inline_data, dict):
            continue
        encoded_audio = inline_data.get("data")
        mime_type = inline_data.get("mimeType") or inline_data.get("mime_type")
        if isinstance(encoded_audio, str) and isinstance(mime_type, str):
            try:
                audio = base64.b64decode(encoded_audio, validate=True)
            except (ValueError, TypeError) as exc:
                raise GoogleVertexGeminiTtsError("Vertex returned invalid base64 audio.") from exc
            if audio and len(audio) % 2 == 0:
                return audio, mime_type
    raise GoogleVertexGeminiTtsError("Vertex response did not contain valid PCM audio.")


def _sample_rate_from_mime_type(mime_type: str) -> int:
    match = re.search(r"(?:rate|samplerate)=(\d+)", mime_type, flags=re.IGNORECASE)
    return int(match.group(1)) if match else 24_000


def _write_pcm16_wav(path: Path, audio: bytes, sample_rate_hz: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate_hz)
        wav_file.writeframes(audio)


def _sanitized_error_message(
    response: _HttpResponse,
    model: str,
    location: str,
) -> str:
    return (
        f"Vertex Gemini TTS failed: http={response.status_code}; "
        f"status={response.error_status or 'unknown'}; model={model}; location={location}; "
        f"message={response.error_message or 'none'}"
    )
