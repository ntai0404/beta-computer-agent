from pathlib import Path

import pytest

import beta.infrastructure.llm.google_cloud.multimodal as gcp_multimodal
from beta.infrastructure.llm.google_cloud.multimodal import (
    GcloudCommandResult,
    GoogleCloudMultimodalConfig,
    GoogleCloudMultimodalProvider,
)
from beta.infrastructure.llm.multimodal.base import AnalysisRequest


def test_gcp_health_all_configured_does_not_return_token(monkeypatch):
    calls = []
    exe = r"C:\Google\Cloud SDK\bin\gcloud.cmd"
    monkeypatch.setattr(gcp_multimodal.shutil, "which", lambda name: exe if name == "gcloud.cmd" else None)

    def runner(command, suppress_stdout=False):
        calls.append((tuple(command), suppress_stdout))
        if command[:2] == (exe, "--version"):
            return GcloudCommandResult(tuple(command), 0, "Google Cloud SDK 999.0.0", "")
        if command[:3] == (exe, "auth", "list"):
            return GcloudCommandResult(tuple(command), 0, "user@example.com", "")
        if command[:3] == (exe, "auth", "application-default"):
            assert suppress_stdout is True
            return GcloudCommandResult(tuple(command), 0, "", "")
        if command[:3] == (exe, "config", "get-value"):
            if command[-1] == "ai/region":
                return GcloudCommandResult(tuple(command), 0, "us-east4", "")
            return GcloudCommandResult(tuple(command), 0, "project-a", "")
        raise AssertionError(command)

    provider = GoogleCloudMultimodalProvider(
        config=GoogleCloudMultimodalConfig(location="us-central1", model="gemini-2.5-flash"),
        runner=runner,
    )
    health = provider.health_status()

    assert health.ok()
    assert health.gcloud_cli == "installed_on_path"
    assert health.resolved_executable == exe
    assert health.adc == "adc_available"
    assert health.audio_capability == "unknown_not_verified"
    assert "token" not in repr(health).lower()
    assert any(call[1] for call in calls)


def test_gcp_health_reports_missing_adc_and_unknown_audio(monkeypatch):
    exe = r"C:\Google\Cloud SDK\bin\gcloud.cmd"
    monkeypatch.setattr(gcp_multimodal.shutil, "which", lambda name: exe if name == "gcloud.cmd" else None)

    def runner(command, suppress_stdout=False):
        if command[:2] == (exe, "--version"):
            return GcloudCommandResult(tuple(command), 0, "Google Cloud SDK", "")
        if command[:3] == (exe, "auth", "list"):
            return GcloudCommandResult(tuple(command), 0, "", "")
        if command[:3] == (exe, "auth", "application-default"):
            return GcloudCommandResult(tuple(command), 1, "", "not logged in")
        if command[:3] == (exe, "config", "get-value"):
            return GcloudCommandResult(tuple(command), 0, "(unset)", "")
        raise AssertionError(command)

    provider = GoogleCloudMultimodalProvider(
        config=GoogleCloudMultimodalConfig(location=None, model="text-only-model"),
        runner=runner,
    )
    health = provider.health_status()

    assert not health.ok()
    assert health.active_account == "cli_account_missing"
    assert health.adc == "adc_missing"
    assert health.audio_capability == "unknown_not_verified"
    assert health.adc_error_category == "credentials_missing"


def test_gcp_discovery_installed_not_on_path(monkeypatch, tmp_path: Path):
    fake = tmp_path / "Google" / "Cloud SDK" / "google-cloud-sdk" / "bin" / "gcloud.cmd"
    fake.parent.mkdir(parents=True)
    fake.write_text("@echo off", encoding="utf-8")
    monkeypatch.setattr(gcp_multimodal.shutil, "which", lambda name: None)
    monkeypatch.setattr(gcp_multimodal, "_common_gcloud_paths", lambda: [fake])

    discovery = gcp_multimodal.discover_gcloud_executable()

    assert discovery.status == "installed_not_on_path"
    assert discovery.executable_path == str(fake)


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
