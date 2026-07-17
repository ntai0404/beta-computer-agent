import base64
import wave
from pathlib import Path

import pytest

import beta.infrastructure.speech.tts.google_vertex_gemini as gemini_tts
from beta.interaction.voice.contracts import SpeechRequest


def test_gemini_tts_writes_pcm_response_as_valid_wav(monkeypatch, tmp_path: Path):
    pcm = b"\x00\x00\x01\x00\xff\xff\x00\x00"
    monkeypatch.setattr(
        gemini_tts,
        "_authenticated_json_post",
        lambda *args, **kwargs: gemini_tts._HttpResponse(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "inlineData": {
                                        "data": base64.b64encode(pcm).decode("ascii"),
                                        "mimeType": "audio/L16;rate=24000",
                                    }
                                }
                            ]
                        }
                    }
                ]
            },
        ),
    )
    output = tmp_path / "demo.wav"
    provider = gemini_tts.GoogleVertexGeminiTtsProvider(
        project="project-a",
        location="us-east4",
        model="gemini-2.5-flash-tts",
        style="Energetic and playful.",
    )

    artifact = provider.synthesize(
        SpeechRequest(text="Xin chao", character_profile_id="mambo", output_path=output)
    )

    assert output.exists()
    assert artifact.size_bytes == output.stat().st_size
    assert provider.last_response is not None
    assert provider.last_response.http_status == 200
    assert provider.last_response.mime_type == "audio/L16;rate=24000"
    assert provider.last_response.api_call_count == 1
    assert provider.last_response.prompt_characters > len("Xin chao")
    assert "not a cloned" in artifact.warnings[0]
    with wave.open(str(output), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 24_000
        assert wav_file.readframes(wav_file.getnframes()) == pcm


def test_gemini_tts_returns_sanitized_http_error(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        gemini_tts,
        "_authenticated_json_post",
        lambda *args, **kwargs: gemini_tts._HttpResponse(
            403,
            {},
            "PERMISSION_DENIED",
            "Permission denied for this project.",
        ),
    )
    provider = gemini_tts.GoogleVertexGeminiTtsProvider(
        project="project-a",
        location="us-east4",
        model="gemini-2.5-flash-tts",
        style="Natural.",
    )

    with pytest.raises(gemini_tts.GoogleVertexGeminiTtsError) as error:
        provider.synthesize(
            SpeechRequest(
                text="Xin chao",
                character_profile_id="mambo",
                output_path=tmp_path / "demo.wav",
            )
        )

    assert "http=403" in str(error.value)
    assert "PERMISSION_DENIED" in str(error.value)
    assert "Bearer" not in str(error.value)
