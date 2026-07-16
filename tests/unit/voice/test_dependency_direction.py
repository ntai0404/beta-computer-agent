from pathlib import Path


def test_voice_interaction_layer_does_not_import_google_provider():
    root = Path(__file__).resolve().parents[3]
    for path in (root / "src" / "beta" / "interaction" / "voice").glob("*.py"):
        content = path.read_text(encoding="utf-8")
        assert "google_cloud" not in content
        assert "GoogleCloudMultimodalProvider" not in content
