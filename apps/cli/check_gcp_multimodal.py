"""Health-check Google Cloud multimodal configuration without logging credentials."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT / "src"))

from beta.infrastructure.llm.google_cloud import (  # noqa: E402
    GoogleCloudMultimodalConfig,
    GoogleCloudMultimodalProvider,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Beta Computer Agent - Google Cloud multimodal health check"
    )
    parser.add_argument("--location", help="Override configured Google Cloud location.")
    parser.add_argument("--model", help="Override configured multimodal model.")
    args = parser.parse_args()

    loaded_config = GoogleCloudMultimodalConfig.load(_PROJECT_ROOT)
    config = GoogleCloudMultimodalConfig(
        location=args.location or loaded_config.location,
        model=args.model or loaded_config.model,
        enabled=loaded_config.enabled,
        allow_cloud_upload=False,
        config_file_status=loaded_config.config_file_status,
        location_source="cli_arg" if args.location else loaded_config.location_source,
        model_source="cli_arg" if args.model else loaded_config.model_source,
        upload_source=loaded_config.upload_source,
        enabled_source=loaded_config.enabled_source,
    )
    provider = GoogleCloudMultimodalProvider(config=config)
    health = provider.health_status()

    print("Google Cloud Multimodal Health")
    print(f"gcloud CLI          : {health.gcloud_cli}")
    print(f"resolved executable : {health.resolved_executable or 'none'}")
    print(f"discovery method    : {health.discovery_method}")
    print(f"gcloud version      : {health.version or 'unknown'}")
    print(f"active account      : {health.active_account}")
    print(f"account check       : {health.active_account_check}")
    print(f"ADC                 : {health.adc}")
    print(f"ADC exit code       : {health.adc_exit_code if health.adc_exit_code is not None else 'not_run'}")
    print(f"ADC error category  : {health.adc_error_category or 'none'}")
    print(f"current project     : {health.current_project or 'not_configured'}")
    print(f"project status      : {health.project_status}")
    print(f"configured location : {health.configured_location or 'not_configured'}")
    print(f"location source     : {health.location_source}")
    print(f"configured model    : {health.configured_model or 'not_configured'}")
    print(f"model source        : {health.model_source}")
    print(f"model status        : {health.model_status}")
    print(f"config file         : {health.config_file_status}")
    print(f"config enabled      : {str(health.config_enabled).lower()}")
    print(f"audio capability    : {health.audio_capability}")
    print(f"video capability    : {health.video_capability}")
    print(f"structured output   : {health.structured_output_capability}")
    print(f"cloud media upload  : {health.cloud_media_upload}")
    if health.blockers:
        print("Blockers:")
        for blocker in health.blockers:
            print(f"  - {blocker}")
    if health.warnings:
        print("Warnings:")
        for warning in health.warnings:
            print(f"  - {warning}")

    return 0 if health.ok() else 1


if __name__ == "__main__":
    sys.exit(main())
