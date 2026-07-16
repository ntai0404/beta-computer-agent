"""Google Cloud multimodal provider boundary.

This adapter uses Google Cloud CLI and Application Default Credentials (ADC)
status checks. It never accepts API keys, never logs tokens, and never uploads
local media unless the caller explicitly opts in.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

from beta.infrastructure.llm.multimodal.base import (
    AnalysisCapabilities,
    AnalysisRequest,
    AnalysisResult,
    MediaType,
    MultimodalVoiceAnalyzer,
)
from beta.infrastructure.llm.multimodal.voice_hint_contracts import VoiceHint


@dataclass(frozen=True)
class GcloudCommandResult:
    command: tuple[str, ...]
    returncode: int
    stdout: str = ""
    stderr: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


CommandRunner = Callable[[Sequence[str], bool], GcloudCommandResult]


@dataclass(frozen=True)
class GoogleCloudMultimodalConfig:
    location: str | None = None
    model: str | None = None
    allow_cloud_upload: bool = False

    @classmethod
    def from_environment(cls) -> "GoogleCloudMultimodalConfig":
        return cls(
            location=(
                os.environ.get("GOOGLE_CLOUD_LOCATION")
                or os.environ.get("GOOGLE_VERTEX_LOCATION")
                or os.environ.get("VERTEX_AI_LOCATION")
            ),
            model=(
                os.environ.get("GOOGLE_CLOUD_MULTIMODAL_MODEL")
                or os.environ.get("GOOGLE_VERTEX_MODEL")
                or os.environ.get("VERTEX_AI_MODEL")
            ),
            allow_cloud_upload=os.environ.get("BETA_ALLOW_CLOUD_MEDIA_UPLOAD") == "1",
        )


@dataclass
class GoogleCloudMultimodalHealth:
    gcloud_cli: str
    active_account: str
    adc: str
    current_project: str | None
    configured_location: str | None
    configured_model: str | None
    audio_capability: str
    video_capability: str
    structured_output_capability: str
    warnings: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return (
            self.gcloud_cli == "available"
            and self.active_account == "configured"
            and self.adc == "configured"
            and self.current_project is not None
            and self.configured_location is not None
            and self.configured_model is not None
        )


def _default_runner(command: Sequence[str], suppress_stdout: bool = False) -> GcloudCommandResult:
    try:
        completed = subprocess.run(
            list(command),
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except FileNotFoundError as exc:
        return GcloudCommandResult(tuple(command), 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        return GcloudCommandResult(tuple(command), 124, "", str(exc))
    stdout = "" if suppress_stdout else completed.stdout.strip()
    return GcloudCommandResult(
        command=tuple(command),
        returncode=completed.returncode,
        stdout=stdout,
        stderr=completed.stderr.strip(),
    )


class GoogleCloudMultimodalProvider(MultimodalVoiceAnalyzer):
    def __init__(
        self,
        config: GoogleCloudMultimodalConfig | None = None,
        runner: CommandRunner = _default_runner,
    ) -> None:
        self.config = config or GoogleCloudMultimodalConfig.from_environment()
        self._runner = runner

    @property
    def provider_id(self) -> str:
        return "google-cloud-multimodal"

    def health_status(self) -> GoogleCloudMultimodalHealth:
        warnings: list[str] = []

        version = self._runner(("gcloud", "--version"), False)
        gcloud_cli = "available" if version.ok else "missing_or_unavailable"
        if not version.ok:
            warnings.append("gcloud CLI is not available on PATH.")

        account = self._runner(
            ("gcloud", "auth", "list", "--filter=status:ACTIVE", "--format=value(account)"),
            False,
        )
        active_account = "configured" if account.ok and account.stdout.strip() else "not_configured"
        if active_account != "configured":
            warnings.append("No active gcloud account detected. Beta did not run login.")

        adc = self._runner(("gcloud", "auth", "application-default", "print-access-token"), True)
        adc_status = "configured" if adc.ok else "not_configured"
        if adc_status != "configured":
            warnings.append("Application Default Credentials are not configured. Beta did not run login.")

        project_result = self._runner(("gcloud", "config", "get-value", "project"), False)
        project = project_result.stdout.strip() if project_result.ok else None
        if project in ("", "(unset)", "unset"):
            project = None
            warnings.append("No current Google Cloud project configured.")

        location = self.config.location
        if not location:
            warnings.append(
                "No Google Cloud location configured. Set GOOGLE_CLOUD_LOCATION or GOOGLE_VERTEX_LOCATION."
            )

        model = self.config.model
        if not model:
            warnings.append(
                "No multimodal model configured. Set GOOGLE_CLOUD_MULTIMODAL_MODEL or GOOGLE_VERTEX_MODEL."
            )

        caps = _capabilities_for_model(model)
        if not caps.supports_audio_input:
            warnings.append(
                "Configured provider/model does not declare direct audio input support; "
                "audio analysis must fall back to transcript or metadata."
            )

        return GoogleCloudMultimodalHealth(
            gcloud_cli=gcloud_cli,
            active_account=active_account,
            adc=adc_status,
            current_project=project,
            configured_location=location,
            configured_model=model,
            audio_capability="supported" if caps.supports_audio_input else "not_declared",
            video_capability="supported" if caps.supports_video_input else "not_declared",
            structured_output_capability=(
                "supported" if caps.supports_structured_output else "not_declared"
            ),
            warnings=warnings,
        )

    def capabilities(self) -> AnalysisCapabilities:
        return _capabilities_for_model(self.config.model)

    def health_check(self) -> None:
        health = self.health_status()
        if not health.ok():
            raise RuntimeError("; ".join(health.warnings) or "Google Cloud multimodal is not ready.")

    def analyze_audio(self, request: AnalysisRequest) -> AnalysisResult:
        self._refuse_unapproved_upload(request.reference_path)
        raise NotImplementedError(
            "Google Cloud multimodal audio analysis call is not implemented in this milestone."
        )

    def analyze_video(self, request: AnalysisRequest) -> AnalysisResult:
        self._refuse_unapproved_upload(request.reference_path)
        raise NotImplementedError(
            "Google Cloud multimodal video analysis call is not implemented in this milestone."
        )

    def transcribe(self, request: AnalysisRequest) -> str | None:
        if not self.capabilities().supports_transcription:
            return None
        self._refuse_unapproved_upload(request.reference_path)
        return None

    def supported_media_types(self) -> list[MediaType]:
        caps = self.capabilities()
        media: list[MediaType] = ["text"]
        if caps.supports_audio_input:
            media.append("audio")
        if caps.supports_video_input:
            media.append("video")
        if caps.supports_image_input:
            media.append("image")
        return media

    def _refuse_unapproved_upload(self, reference_path: Path) -> None:
        if not self.config.allow_cloud_upload:
            raise PermissionError(
                f"Cloud media upload is not approved for {reference_path}. "
                "Set allow_cloud_upload=True only after explicit user approval."
            )


def _capabilities_for_model(model: str | None) -> AnalysisCapabilities:
    if not model:
        return AnalysisCapabilities(
            supports_audio_input=False,
            supports_video_input=False,
            supports_image_input=False,
            supports_transcription=False,
            supports_structured_output=False,
            notes="No model configured.",
        )

    normalized = model.lower()
    if normalized.startswith("gemini-"):
        return AnalysisCapabilities(
            supports_audio_input=True,
            supports_video_input=True,
            supports_image_input=True,
            supports_transcription=True,
            supports_structured_output=True,
            supported_audio_formats=["wav", "mp3", "flac", "ogg", "m4a"],
            supported_video_formats=["mp4", "webm", "mkv", "avi"],
            notes=(
                "Capability declared for configured Gemini multimodal model family. "
                "No media is uploaded by health checks."
            ),
        )

    return AnalysisCapabilities(
        supports_audio_input=False,
        supports_video_input=False,
        supports_image_input=False,
        supports_transcription=False,
        supports_structured_output=False,
        notes=f"Model '{model}' is not declared as a supported multimodal audio model.",
    )
