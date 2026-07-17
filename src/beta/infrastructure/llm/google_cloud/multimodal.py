"""Google Cloud multimodal provider boundary.

This adapter uses Google Cloud CLI and Application Default Credentials (ADC)
status checks. It never accepts API keys, never logs tokens, and never uploads
local media unless the caller explicitly opts in.
"""

from __future__ import annotations

import os
import json
import re
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

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
    enabled: bool = False
    allow_cloud_upload: bool = False
    config_file_status: str = "not_checked"
    location_source: str = "missing"
    model_source: str = "missing"
    upload_source: str = "default_false"
    enabled_source: str = "default_false"

    @classmethod
    def from_environment(cls) -> "GoogleCloudMultimodalConfig":
        location = (
            os.environ.get("GOOGLE_CLOUD_LOCATION")
            or os.environ.get("GOOGLE_VERTEX_LOCATION")
            or os.environ.get("VERTEX_AI_LOCATION")
        )
        model = (
            os.environ.get("GOOGLE_CLOUD_MULTIMODAL_MODEL")
            or os.environ.get("GOOGLE_VERTEX_MODEL")
            or os.environ.get("VERTEX_AI_MODEL")
        )
        return cls(
            location=location,
            model=model,
            allow_cloud_upload=os.environ.get("BETA_ALLOW_CLOUD_MEDIA_UPLOAD") == "1",
            config_file_status="not_checked",
            location_source="environment" if location else "missing",
            model_source="environment" if model else "missing",
            upload_source=(
                "environment" if os.environ.get("BETA_ALLOW_CLOUD_MEDIA_UPLOAD") == "1"
                else "default_false"
            ),
        )

    @classmethod
    def load(cls, project_root: Path | None = None) -> "GoogleCloudMultimodalConfig":
        """Load config using precedence: config file, environment, then gcloud for location."""
        env_config = cls.from_environment()
        config_path = (project_root or Path.cwd()) / "config" / "user" / "gcp-multimodal.json"
        file_data: dict = {}
        config_file_status = "missing"
        if config_path.exists():
            try:
                file_data = json.loads(config_path.read_text(encoding="utf-8-sig"))
                config_file_status = "loaded"
            except (OSError, json.JSONDecodeError):
                config_file_status = "invalid"

        location = _first_non_empty(file_data.get("location"), env_config.location)
        model = _first_non_empty(
            file_data.get("model_id"),
            file_data.get("model"),
            env_config.model,
        )
        enabled = bool(file_data.get("enabled", False))
        allow_cloud_upload = bool(
            file_data.get("allow_audio_upload", False)
            or file_data.get("allow_cloud_upload", False)
            or env_config.allow_cloud_upload
        )

        return cls(
            location=location,
            model=model,
            enabled=enabled,
            allow_cloud_upload=allow_cloud_upload,
            config_file_status=config_file_status,
            location_source=(
                "config_file" if _first_non_empty(file_data.get("location")) else
                env_config.location_source
            ),
            model_source=(
                "config_file" if _first_non_empty(file_data.get("model_id"), file_data.get("model"))
                else env_config.model_source
            ),
            upload_source=(
                "config_file" if (
                    "allow_audio_upload" in file_data or "allow_cloud_upload" in file_data
                ) else env_config.upload_source
            ),
            enabled_source="config_file" if "enabled" in file_data else "default_false",
        )


@dataclass
class GoogleCloudMultimodalHealth:
    gcloud_cli: str
    resolved_executable: str | None
    discovery_method: str
    version: str | None
    active_account: str
    active_account_check: str
    adc: str
    adc_exit_code: int | None
    adc_error_category: str | None
    current_project: str | None
    project_status: str
    configured_location: str | None
    location_source: str
    configured_model: str | None
    model_source: str
    model_status: str
    config_enabled: bool
    config_file_status: str
    cloud_media_upload: str
    audio_capability: str
    video_capability: str
    structured_output_capability: str
    texttospeech_api_enabled: str = "not_checked"
    aiplatform_api_enabled: str = "not_checked"
    generativelanguage_api_enabled: str = "not_checked"
    service_identity_ready: str = "not_checked"
    iam_ready: str = "not_checked"
    iam_details: str = "not_checked"
    quota_ready: str = "not_checked"
    gemini_tts_available: str = "not_checked"
    instant_custom_voice_method_exposed: str = "not_checked"
    instant_custom_voice_allowlisted: str = "not_checked"
    instant_custom_voice_blocker: str = "not_checked"
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def ok(self) -> bool:
        return (
            self.gcloud_cli in ("installed_on_path", "installed_not_on_path")
            and self.active_account == "authenticated_cli"
            and self.adc == "adc_available"
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


@dataclass(frozen=True)
class GoogleCloudHttpResult:
    status_code: int
    error_status: str | None = None
    error_message: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GoogleCloudTtsReadiness:
    texttospeech_api_enabled: str = "not_checked"
    aiplatform_api_enabled: str = "not_checked"
    generativelanguage_api_enabled: str = "not_checked"
    service_identity_ready: str = "not_checked"
    iam_ready: str = "not_checked"
    iam_details: str = "not_checked"
    quota_ready: str = "not_checked"
    gemini_tts_available: str = "not_checked"
    instant_custom_voice_method_exposed: str = "not_checked"
    instant_custom_voice_allowlisted: str = "not_checked"
    instant_custom_voice_blocker: str = "not_checked"

    @classmethod
    def not_checked(cls) -> "GoogleCloudTtsReadiness":
        return cls()


class GoogleCloudMultimodalProvider(MultimodalVoiceAnalyzer):
    def __init__(
        self,
        config: GoogleCloudMultimodalConfig | None = None,
        runner: CommandRunner = _default_runner,
        verify_tts_capabilities: bool = False,
    ) -> None:
        self.config = config or GoogleCloudMultimodalConfig.from_environment()
        self._runner = runner
        self._verify_tts_capabilities = verify_tts_capabilities

    @property
    def provider_id(self) -> str:
        return "google-cloud-multimodal"

    def health_status(self) -> GoogleCloudMultimodalHealth:
        warnings: list[str] = []
        blockers: list[str] = []

        discovery = discover_gcloud_executable()
        gcloud_cli = discovery.status
        executable = discovery.executable_path
        version_text = None
        version_result = None
        if executable:
            version_result = self._runner((executable, "--version"), False)
            version_text = _extract_gcloud_version(version_result.stdout)
            if not version_result.ok:
                gcloud_cli = "executable_found_but_failed"
                blockers.append("gcloud_executable_failed")
        else:
            blockers.append("gcloud_not_installed")
            warnings.append("gcloud CLI was not found on PATH or common Windows install paths.")

        account = _missing_result("auth list")
        project_result = _missing_result("config get-value project")
        location_result = _missing_result("config get-value ai/region")
        adc = _missing_result("application-default print-access-token")
        if executable:
            account = self._runner(
                (
                    executable,
                    "auth",
                    "list",
                    "--filter=status:ACTIVE",
                    "--format=value(account)",
                ),
                False,
            )
            project_result = self._runner((executable, "config", "get-value", "project"), False)
            location_result = self._runner((executable, "config", "get-value", "ai/region"), False)
            adc = self._runner(
                (executable, "auth", "application-default", "print-access-token"),
                True,
            )

        active_account = (
            "authenticated_cli"
            if account.ok and account.stdout.strip()
            else "cli_account_missing"
        )
        active_account_check = "ok" if account.ok else _error_category(account)
        if active_account != "authenticated_cli":
            blockers.append("cli_account_missing")
            warnings.append("No active gcloud account detected. Beta did not run login.")

        adc_status = "adc_available" if adc.ok else "adc_missing"
        adc_error_category = None if adc.ok else _error_category(adc)
        if adc_status != "adc_available":
            blockers.append("adc_missing")
            warnings.append("Application Default Credentials are not available. Beta did not run login.")

        project = project_result.stdout.strip() if project_result.ok else None
        if project in ("", "(unset)", "unset"):
            project = None
        project_status = "project_configured" if project else "project_missing"
        if project is None:
            blockers.append("project_missing")
            warnings.append("No current Google Cloud project configured.")

        location = self.config.location
        location_source = self.config.location_source
        gcloud_location = location_result.stdout.strip() if location_result.ok else None
        if gcloud_location in ("", "(unset)", "unset"):
            gcloud_location = None
        if not location and gcloud_location:
            location = gcloud_location
            location_source = "gcloud_active_configuration:ai/region"
        if not location:
            blockers.append("location_missing")
            warnings.append(
                "No Google Cloud location configured. Set GOOGLE_CLOUD_LOCATION or GOOGLE_VERTEX_LOCATION."
            )

        model = self.config.model
        model_status = "model_configured" if model else "model_missing"
        if not model:
            blockers.append("model_missing")
            warnings.append(
                "No multimodal model configured. Set GOOGLE_CLOUD_MULTIMODAL_MODEL or GOOGLE_VERTEX_MODEL."
            )

        caps = _capabilities_for_model(model)
        audio_capability = (
            "model_missing" if not model else "unknown_not_verified"
        )
        video_capability = (
            "model_missing" if not model else "unknown_not_verified"
        )
        structured_output_capability = (
            "model_missing" if not model else "unknown_not_verified"
        )
        if audio_capability != "supported":
            warnings.append(
                "Audio capability was not verified by provider metadata; "
                "audio analysis must not upload media or fake results."
            )

        tts_readiness = GoogleCloudTtsReadiness.not_checked()
        if self._verify_tts_capabilities:
            tts_readiness = _verify_google_tts_readiness(
                runner=self._runner,
                executable=executable,
                project=project,
                location=location,
            )
            if tts_readiness.instant_custom_voice_blocker not in ("none", "not_checked"):
                blockers.append(tts_readiness.instant_custom_voice_blocker)

        return GoogleCloudMultimodalHealth(
            gcloud_cli=gcloud_cli,
            resolved_executable=executable,
            discovery_method=discovery.method,
            version=version_text,
            active_account=active_account,
            active_account_check=active_account_check,
            adc=adc_status,
            adc_exit_code=adc.returncode if executable else None,
            adc_error_category=adc_error_category,
            current_project=project,
            project_status=project_status,
            configured_location=location,
            location_source=location_source,
            configured_model=model,
            model_source=self.config.model_source,
            model_status=model_status,
            config_enabled=self.config.enabled,
            config_file_status=self.config.config_file_status,
            cloud_media_upload="enabled" if self.config.allow_cloud_upload else "disabled",
            audio_capability=audio_capability,
            video_capability=video_capability,
            structured_output_capability=structured_output_capability,
            texttospeech_api_enabled=tts_readiness.texttospeech_api_enabled,
            aiplatform_api_enabled=tts_readiness.aiplatform_api_enabled,
            generativelanguage_api_enabled=tts_readiness.generativelanguage_api_enabled,
            service_identity_ready=tts_readiness.service_identity_ready,
            iam_ready=tts_readiness.iam_ready,
            iam_details=tts_readiness.iam_details,
            quota_ready=tts_readiness.quota_ready,
            gemini_tts_available=tts_readiness.gemini_tts_available,
            instant_custom_voice_method_exposed=tts_readiness.instant_custom_voice_method_exposed,
            instant_custom_voice_allowlisted=tts_readiness.instant_custom_voice_allowlisted,
            instant_custom_voice_blocker=tts_readiness.instant_custom_voice_blocker,
            blockers=blockers,
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

    return AnalysisCapabilities(
        supports_audio_input=False,
        supports_video_input=False,
        supports_image_input=False,
        supports_transcription=False,
        supports_structured_output=False,
        notes=(
            f"Model '{model}' capability has not been verified by provider metadata. "
            "Do not infer audio support from the model name."
        ),
    )


def _verify_google_tts_readiness(
    *,
    runner: CommandRunner,
    executable: str | None,
    project: str | None,
    location: str | None,
) -> GoogleCloudTtsReadiness:
    """Run non-media TTS checks without logging credentials or error bodies."""
    if not executable or not project:
        return GoogleCloudTtsReadiness(
            instant_custom_voice_blocker="prerequisites_missing",
        )

    service_states = {
        service: _enabled_service_status(runner, executable, project, service)
        for service in (
            "texttospeech.googleapis.com",
            "aiplatform.googleapis.com",
            "generativelanguage.googleapis.com",
        )
    }
    service_identity_ready = _aiplatform_service_identity_status(runner, executable, project)
    quota_ready = _tts_quota_status(runner, executable, project)

    service_usage_permissions = _project_permission_status(
        project,
        ("serviceusage.services.enable", "serviceusage.services.get"),
    )
    vertex_endpoint_permission = _project_permission_status(
        project,
        ("aiplatform.endpoints.predict",),
    )
    voices_list = _authenticated_json_request(
        "GET",
        "https://texttospeech.googleapis.com/v1/voices?languageCode=ja-JP",
        project,
    )
    synthesize_empty = _authenticated_json_request(
        "POST",
        "https://texttospeech.googleapis.com/v1/text:synthesize",
        project,
        {},
    )
    tts_authorized = (
        voices_list.status_code == 200
        and synthesize_empty.status_code == 400
        and synthesize_empty.error_status == "INVALID_ARGUMENT"
    )
    iam_ready = (
        service_usage_permissions == "granted"
        and vertex_endpoint_permission == "granted"
        and tts_authorized
    )
    iam_details = "; ".join(
        (
            f"serviceusage={service_usage_permissions}",
            f"aiplatform.endpoints.predict={vertex_endpoint_permission}",
            "aiplatform.models.predict=not_testable_on_project_resource",
            f"texttospeech.voices.list={'granted' if voices_list.status_code == 200 else _http_status(voices_list)}",
            f"texttospeech.text.synthesize={'granted_schema_validation' if tts_authorized else _http_status(synthesize_empty)}",
        )
    )

    gemini_tts_available = _gemini_tts_status(project, location)
    (
        instant_custom_voice_method_exposed,
        instant_custom_voice_allowlisted,
        instant_custom_voice_blocker,
    ) = _instant_custom_voice_status(project)

    return GoogleCloudTtsReadiness(
        texttospeech_api_enabled=service_states["texttospeech.googleapis.com"],
        aiplatform_api_enabled=service_states["aiplatform.googleapis.com"],
        generativelanguage_api_enabled=service_states["generativelanguage.googleapis.com"],
        service_identity_ready=service_identity_ready,
        iam_ready="true" if iam_ready else "false",
        iam_details=iam_details,
        quota_ready=quota_ready,
        gemini_tts_available=gemini_tts_available,
        instant_custom_voice_method_exposed=instant_custom_voice_method_exposed,
        instant_custom_voice_allowlisted=instant_custom_voice_allowlisted,
        instant_custom_voice_blocker=instant_custom_voice_blocker,
    )


def _enabled_service_status(
    runner: CommandRunner,
    executable: str,
    project: str,
    service: str,
) -> str:
    result = runner(
        (
            executable,
            "services",
            "list",
            "--enabled",
            f"--project={project}",
            f"--filter=config.name={service}",
            "--format=value(config.name)",
        ),
        False,
    )
    if not result.ok:
        return "unknown"
    return "true" if service in result.stdout.splitlines() else "false"


def _aiplatform_service_identity_status(
    runner: CommandRunner,
    executable: str,
    project: str,
) -> str:
    result = runner(
        (executable, "projects", "get-iam-policy", project, "--format=json"),
        False,
    )
    if not result.ok:
        return "unknown"
    try:
        bindings = json.loads(result.stdout).get("bindings", [])
    except json.JSONDecodeError:
        return "unknown"
    return "true" if any(
        binding.get("role") == "roles/aiplatform.serviceAgent" for binding in bindings
    ) else "false"


def _tts_quota_status(runner: CommandRunner, executable: str, project: str) -> str:
    project_number = runner(
        (executable, "projects", "describe", project, "--format=value(projectNumber)"),
        False,
    )
    if not project_number.ok or not project_number.stdout.strip():
        return "unknown"
    quota = runner(
        (
            executable,
            "alpha",
            "services",
            "quota",
            "list",
            "--service=texttospeech.googleapis.com",
            f"--consumer=projects/{project_number.stdout.strip()}",
            "--format=json",
        ),
        False,
    )
    if not quota.ok:
        return "unknown"
    try:
        entries = json.loads(quota.stdout)
    except json.JSONDecodeError:
        return "unknown"

    required_metrics = {
        "texttospeech.googleapis.com/requests_chirpvoicecloning",
        "texttospeech.googleapis.com/requests_generatevoicecloningkey",
    }
    available_metrics: set[str] = set()
    for entry in entries:
        metric = entry.get("metric")
        for limit in entry.get("consumerQuotaLimits", []):
            for bucket in limit.get("quotaBuckets", []):
                if _positive_quota_limit(bucket.get("effectiveLimit")):
                    available_metrics.add(metric)
    return "true" if required_metrics.issubset(available_metrics) else "false"


def _positive_quota_limit(value: object) -> bool:
    try:
        return int(str(value)) > 0
    except (TypeError, ValueError):
        return False


def _project_permission_status(project: str, permissions: tuple[str, ...]) -> str:
    result = _authenticated_json_request(
        "POST",
        f"https://cloudresourcemanager.googleapis.com/v1/projects/{project}:testIamPermissions",
        project,
        {"permissions": list(permissions)},
    )
    if result.status_code != 200:
        return _http_status(result)
    granted = set(result.payload.get("permissions", []))
    return "granted" if granted.issuperset(permissions) else "not_granted"


def _gemini_tts_status(project: str, location: str | None) -> str:
    if not location:
        return "location_missing"
    endpoint = (
        "aiplatform.googleapis.com"
        if location == "global"
        else f"{location}-aiplatform.googleapis.com"
    )
    responses = [
        _authenticated_json_request(
            "POST",
            (
                f"https://{endpoint}/v1beta1/projects/{project}/locations/{location}"
                f"/publishers/google/models/{model}:generateContent"
            ),
            project,
            {},
        )
        for model in ("gemini-2.5-flash-tts", "gemini-2.5-pro-tts")
    ]
    if all(
        response.status_code == 400 and response.error_status == "INVALID_ARGUMENT"
        for response in responses
    ):
        return "true"
    if any(response.status_code == 403 for response in responses):
        return "false_permission_or_entitlement"
    if any(response.status_code == 404 for response in responses):
        return "false_model_or_region_unavailable"
    return "unknown"


def _instant_custom_voice_status(project: str) -> tuple[str, str, str]:
    endpoints = (
        "https://texttospeech.googleapis.com",
        "https://us-texttospeech.googleapis.com",
        "https://eu-texttospeech.googleapis.com",
        "https://asia-southeast1-texttospeech.googleapis.com",
        "https://asia-northeast1-texttospeech.googleapis.com",
        "https://europe-west2-texttospeech.googleapis.com",
    )
    responses = [
        _authenticated_json_request(
            "POST",
            f"{endpoint}/v1beta1/voices:generateVoiceCloningKey",
            project,
            {},
        )
        for endpoint in endpoints
    ]
    if all(
        response.status_code == 404 and response.error_status == "NOT_FOUND"
        for response in responses
    ):
        return (
            "false",
            "false_or_not_exposed",
            "external_entitlement_not_cli_enablement",
        )
    if any(
        response.status_code == 400 and response.error_status == "INVALID_ARGUMENT"
        for response in responses
    ):
        return (
            "true",
            "not_verifiable_without_valid_consent_request",
            "valid_voice_owner_consent_required",
        )
    if any(response.status_code == 403 for response in responses):
        return (
            "unknown",
            "unknown_permission_or_entitlement",
            "permission_or_external_entitlement",
        )
    if any(response.status_code == 429 for response in responses):
        return "unknown", "unknown_quota_exhausted", "quota_exhausted"
    return "unknown", "unknown", "endpoint_probe_inconclusive"


def _authenticated_json_request(
    method: str,
    url: str,
    project: str,
    payload: dict[str, Any] | None = None,
) -> GoogleCloudHttpResult:
    """Make an ADC request while keeping access tokens and bodies out of health output."""
    try:
        import google.auth
        import google.auth.transport.requests

        credentials, _ = google.auth.default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        credentials.refresh(google.auth.transport.requests.Request())
    except Exception as exc:  # pragma: no cover - environment-specific ADC errors
        return GoogleCloudHttpResult(0, type(exc).__name__, "ADC unavailable")

    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(url, data=data, method=method)
    request.add_header("Authorization", f"Bearer {credentials.token}")
    request.add_header("x-goog-user-project", project)
    if payload is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return GoogleCloudHttpResult(response.status, payload=_read_json(response.read()))
    except urllib.error.HTTPError as exc:
        body = _read_json(exc.read())
        error = body.get("error", {})
        return GoogleCloudHttpResult(
            exc.code,
            str(error.get("status") or "HTTP_ERROR"),
            str(error.get("message") or "")[:300],
            body,
        )
    except (urllib.error.URLError, TimeoutError) as exc:
        return GoogleCloudHttpResult(0, type(exc).__name__, "request unavailable")


def _read_json(raw: bytes) -> dict[str, Any]:
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _http_status(result: GoogleCloudHttpResult) -> str:
    if result.status_code == 0:
        return result.error_status or "unavailable"
    return f"http_{result.status_code}_{result.error_status or 'unknown'}"


@dataclass(frozen=True)
class GcloudDiscovery:
    status: str
    executable_path: str | None
    method: str


def discover_gcloud_executable() -> GcloudDiscovery:
    path_hit = shutil.which("gcloud.cmd") or shutil.which("gcloud")
    if path_hit:
        return GcloudDiscovery(
            status="installed_on_path",
            executable_path=str(Path(path_hit)),
            method="shutil.which",
        )

    common_paths = _common_gcloud_paths()
    for path in common_paths:
        if path.exists():
            return GcloudDiscovery(
                status="installed_not_on_path",
                executable_path=str(path),
                method="common_windows_install_path",
            )

    return GcloudDiscovery(
        status="not_installed",
        executable_path=None,
        method="path_and_common_windows_install_paths",
    )


def _common_gcloud_paths() -> list[Path]:
    candidates = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    program_files_x86 = os.environ.get("ProgramFiles(x86)")
    user_profile = os.environ.get("USERPROFILE")
    for root in (local_app_data, program_files, program_files_x86):
        if root:
            candidates.append(Path(root) / "Google" / "Cloud SDK" / "google-cloud-sdk" / "bin" / "gcloud.cmd")
    if user_profile:
        candidates.append(
            Path(user_profile)
            / "AppData"
            / "Local"
            / "Google"
            / "Cloud SDK"
            / "google-cloud-sdk"
            / "bin"
            / "gcloud.cmd"
        )
    return candidates


def _extract_gcloud_version(stdout: str) -> str | None:
    match = re.search(r"Google Cloud SDK\s+([^\r\n]+)", stdout)
    return match.group(1).strip() if match else None


def _error_category(result: GcloudCommandResult) -> str:
    text = f"{result.stderr}\n{result.stdout}".lower()
    if result.returncode == 127:
        return "executable_not_found"
    if result.returncode == 124:
        return "timeout"
    if "access is denied" in text or "permission denied" in text:
        return "permission_denied"
    if "not logged in" in text or "no credential" in text:
        return "credentials_missing"
    if "network" in text or "could not" in text or "unavailable" in text:
        return "unavailable"
    return f"exit_code_{result.returncode}"


def _missing_result(command_name: str) -> GcloudCommandResult:
    return GcloudCommandResult((command_name,), 127, "", "gcloud executable not resolved")


def _first_non_empty(*values: object) -> str | None:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return None
