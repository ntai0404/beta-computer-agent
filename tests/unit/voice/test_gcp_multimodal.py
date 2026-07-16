from pathlib import Path

import pytest

from beta.infrastructure.llm.google_cloud.multimodal import (
    GcloudCommandResult,
    GoogleCloudMultimodalConfig,
    GoogleCloudMultimodalProvider,
)
from beta.infrastructure.llm.multimodal.base import AnalysisRequest


def test_gcp_health_all_configured_does_not_return_token():
    calls = []

    def runner(command, suppress_stdout=False):
        calls.append((tuple(command), suppress_stdout))
        if command[:2] == ("gcloud", "--version"):
            return GcloudCommandResult(tuple(command), 0, "Google Cloud SDK 999.0.0", "")
        if command[:3] == ("gcloud", "auth", "list"):
            return GcloudCommandResult(tuple(command), 0, "user@example.com", "")
        if command[:3] == ("gcloud", "auth", "application-default"):
            assert suppress_stdout is True
            return GcloudCommandResult(tuple(command), 0, "", "")
        if command[:3] == ("gcloud", "config", "get-value"):
            return GcloudCommandResult(tuple(command), 0, "project-a", "")
        raise AssertionError(command)

    provider = GoogleCloudMultimodalProvider(
        config=GoogleCloudMultimodalConfig(location="us-central1", model="gemini-2.5-flash"),
        runner=runner,
    )
    health = provider.health_status()

    assert health.ok()
    assert health.adc == "configured"
    assert health.audio_capability == "supported"
    assert "token" not in repr(health).lower()
    assert any(call[1] for call in calls)


def test_gcp_health_reports_missing_adc_and_unknown_audio():
    def runner(command, suppress_stdout=False):
        if command[:2] == ("gcloud", "--version"):
            return GcloudCommandResult(tuple(command), 0, "Google Cloud SDK", "")
        if command[:3] == ("gcloud", "auth", "list"):
            return GcloudCommandResult(tuple(command), 0, "", "")
        if command[:3] == ("gcloud", "auth", "application-default"):
            return GcloudCommandResult(tuple(command), 1, "", "not logged in")
        if command[:3] == ("gcloud", "config", "get-value"):
            return GcloudCommandResult(tuple(command), 0, "(unset)", "")
        raise AssertionError(command)

    provider = GoogleCloudMultimodalProvider(
        config=GoogleCloudMultimodalConfig(location=None, model="text-only-model"),
        runner=runner,
    )
    health = provider.health_status()

    assert not health.ok()
    assert health.active_account == "not_configured"
    assert health.adc == "not_configured"
    assert health.audio_capability == "not_declared"


def test_gcp_provider_refuses_cloud_upload_without_approval(tmp_path: Path):
    audio = tmp_path / "clip.wav"
    audio.write_bytes(b"RIFF")
    provider = GoogleCloudMultimodalProvider(
        config=GoogleCloudMultimodalConfig(
            location="us-central1",
            model="gemini-2.5-flash",
            allow_cloud_upload=False,
        ),
        runner=lambda command, suppress_stdout=False: GcloudCommandResult(tuple(command), 0, "ok", ""),
    )

    request = AnalysisRequest(
        reference_path=audio,
        character_profile_id="mambo",
        persona_alias="Mambo",
    )
    with pytest.raises(PermissionError, match="Cloud media upload is not approved"):
        provider.analyze_audio(request)
