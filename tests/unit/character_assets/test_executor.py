import json
from pathlib import Path

import pytest
from beta.infrastructure.character_assets.importers.executor import ImportExecutor
from beta.infrastructure.character_assets.validation.security import compute_sha256


def test_import_executor_dry_run(tmp_path: Path):
    project_root = tmp_path / "project"
    var_assets = project_root / "var" / "assets" / "characters" / "mambo"
    artifacts_dir = project_root / "var" / "artifacts"
    import_dir = artifacts_dir / "character-import" / "mambo"
    import_dir.mkdir(parents=True, exist_ok=True)
    
    # Fake source file
    source_file = tmp_path / "sprite.png"
    source_file.write_text("fake png")
    checksum = compute_sha256(source_file)
    
    # Import plan
    plan = [
        {
            "source_path": str(source_file),
            "destination_path": str(var_assets / "avatar" / "sprite.png"),
            "original_filename": "sprite.png",
            "checksum": checksum,
            "asset_type": "avatar_candidate"
        }
    ]
    plan_path = tmp_path / "import-plan.json"
    plan_path.write_text(json.dumps(plan))
    
    # Mock project root inside executor
    executor = ImportExecutor("mambo", plan_path, artifacts_dir)
    executor.assets_root = var_assets
    executor.project_root = project_root
    
    # Execute dry run
    var_assets.mkdir(parents=True, exist_ok=True)
    results = executor.execute(["sprite.png"], dry_run=True)
    
    assert len(results["imported"]) == 1
    assert not (var_assets / "avatar" / "sprite.png").exists() # Should not actually copy
    
    summary = json.loads((import_dir / "dry-run-import-summary.json").read_text())
    assert summary["status"] == "dry_run"
    assert summary["imported_count"] == 1


def test_import_executor_actual_copy(tmp_path: Path):
    project_root = tmp_path / "project"
    var_assets = project_root / "var" / "assets" / "characters" / "mambo"
    artifacts_dir = project_root / "var" / "artifacts"
    
    source_file = tmp_path / "model.pth"
    source_file.write_text("fake model data")
    checksum = compute_sha256(source_file)
    
    plan = [
        {
            "source_path": str(source_file),
            "destination_path": str(var_assets / "models" / "rvc" / "model.pth"),
            "original_filename": "model.pth",
            "checksum": checksum,
            "asset_type": "rvc_candidate"
        }
    ]
    plan_path = tmp_path / "import-plan.json"
    plan_path.write_text(json.dumps(plan))
    
    executor = ImportExecutor("mambo", plan_path, artifacts_dir)
    executor.assets_root = var_assets
    executor.project_root = project_root
    
    var_assets.mkdir(parents=True, exist_ok=True)
    results = executor.execute(["model.pth"], dry_run=False)
    
    assert len(results["imported"]) == 1
    dest_path = var_assets / "models" / "rvc" / "model.pth"
    assert dest_path.exists()
    assert dest_path.read_text() == "fake model data"
    
    # Check manifest
    import_dir = artifacts_dir / "character-import" / "mambo"
    rollback = json.loads((import_dir / "rollback-manifest.json").read_text())
    assert len(rollback) == 1
    assert rollback[0]["checksum"] == checksum


def test_import_executor_already_present(tmp_path: Path):
    project_root = tmp_path / "project"
    var_assets = project_root / "var" / "assets" / "characters" / "mambo"
    artifacts_dir = project_root / "var" / "artifacts"
    
    source_file = tmp_path / "clip.wav"
    source_file.write_text("audio")
    checksum = compute_sha256(source_file)
    
    # Create destination beforehand
    dest_path = var_assets / "references" / "audio" / "clip.wav"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text("audio")
    
    plan = [
        {
            "source_path": str(source_file),
            "destination_path": str(dest_path),
            "original_filename": "clip.wav",
            "checksum": checksum,
            "asset_type": "voice_candidate"
        }
    ]
    plan_path = tmp_path / "import-plan.json"
    plan_path.write_text(json.dumps(plan))
    
    executor = ImportExecutor("mambo", plan_path, artifacts_dir)
    executor.assets_root = var_assets
    executor.project_root = project_root
    
    results = executor.execute(["clip.wav"], dry_run=False)
    
    assert len(results["already_present"]) == 1
    assert len(results["imported"]) == 0


def test_import_executor_conflict(tmp_path: Path):
    project_root = tmp_path / "project"
    var_assets = project_root / "var" / "assets" / "characters" / "mambo"
    artifacts_dir = project_root / "var" / "artifacts"
    
    source_file = tmp_path / "clip.wav"
    source_file.write_text("new audio")
    checksum = compute_sha256(source_file)
    
    # Destination has DIFFERENT content
    dest_path = var_assets / "references" / "audio" / "clip.wav"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    dest_path.write_text("old audio")
    
    plan = [
        {
            "source_path": str(source_file),
            "destination_path": str(dest_path),
            "original_filename": "clip.wav",
            "checksum": checksum,
            "asset_type": "voice_candidate"
        }
    ]
    plan_path = tmp_path / "import-plan.json"
    plan_path.write_text(json.dumps(plan))
    
    executor = ImportExecutor("mambo", plan_path, artifacts_dir)
    executor.assets_root = var_assets
    executor.project_root = project_root
    
    results = executor.execute(["clip.wav"], dry_run=False)
    
    assert len(results["conflict"]) == 1
    assert dest_path.read_text() == "old audio" # Must not overwrite
