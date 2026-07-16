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

    env_config = GoogleCloudMultimodalConfig.from_environment()
    config = GoogleCloudMultimodalConfig(
        location=args.location or env_config.location,
        model=args.model or env_config.model,
        allow_cloud_upload=False,
    )
    provider = GoogleCloudMultimodalProvider(config=config)
    health = provider.health_status()

    print("Google Cloud Multimodal Health")
    print(f"gcloud CLI          : {health.gcloud_cli}")
    print(f"active account      : {health.active_account}")
    print(f"ADC                 : {health.adc}")
    print(f"current project     : {health.current_project or 'not_configured'}")
    print(f"configured location : {health.configured_location or 'not_configured'}")
    print(f"configured model    : {health.configured_model or 'not_configured'}")
    print(f"audio capability    : {health.audio_capability}")
    print(f"video capability    : {health.video_capability}")
    print(f"structured output   : {health.structured_output_capability}")
    print("cloud media upload  : disabled")
    if health.warnings:
        print("Warnings:")
        for warning in health.warnings:
            print(f"  - {warning}")

    return 0 if health.ok() else 1


if __name__ == "__main__":
    sys.exit(main())
