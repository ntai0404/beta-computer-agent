import json
from pathlib import Path

import pytest
from beta.infrastructure.character_assets.importers.planner import ImportPlanner


def test_import_planner_end_to_end(tmp_path: Path):
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    
    # Create fake desktop gremlin source
    dg_source = tmp_path / "dg"
    dg_models = dg_source / "Models" / "matikanetannhauser"
    dg_models.mkdir(parents=True)
    (dg_models / "sprite.png").write_text("fake png")
    (dg_source / "config.txt").write_text("character=matikanetannhauser")
    
    # Create fake voice dataset source
    voice_source = tmp_path / "voice"
    voice_source.mkdir()
    (voice_source / "clip1.wav").write_text("fake wav")
    (voice_source / "metadata.json").write_text('{"character_name": "matikanetannhauser"}')
    
    # Create fake rvc model source
    rvc_source = tmp_path / "rvc"
    rvc_source.mkdir()
    (rvc_source / "matikanetannhauser_v2.pth").write_text("fake pth")
    
    # Initialize Planner
    planner = ImportPlanner("mambo", "Mambo", artifacts_dir)
    
    # Run inspections
    planner.inspect_sources(
        desktop_gremlin_path=dg_source,
        voice_dataset_path=voice_source,
        rvc_model_path=rvc_source
    )
    
    # Generate reports
    planner.generate_reports()
    
    output_dir = artifacts_dir / "character-inspection" / "mambo"
    
    # Verify JSON outputs exist
    assert (output_dir / "identity-evidence.json").exists()
    assert (output_dir / "inspection-summary.json").exists()
    assert (output_dir / "avatar-inventory.json").exists()
    assert (output_dir / "voice-inventory.json").exists()
    assert (output_dir / "model-inventory.json").exists()
    assert (output_dir / "import-plan.json").exists()
    assert (output_dir / "profile-update-proposal.json").exists()
    
    # Check identity resolution
    identity_data = json.loads((output_dir / "identity-evidence.json").read_text())
    assert identity_data["resolution_status"] == "verified"
    assert identity_data["canonical_character_id"] == "matikanetannhauser"
    
    # Check pipeline recommendation
    summary_data = json.loads((output_dir / "inspection-summary.json").read_text(encoding="utf-8"))
    assert summary_data["voice_pipeline_recommendation"]["recommendation"] == "Base TTS -> RVC"
    
    # Check import plan
    import_plan = json.loads((output_dir / "import-plan.json").read_text(encoding="utf-8"))
    assert len(import_plan) == 5 # 1 png, 1 config, 1 wav, 1 json, 1 pth
    
    png_entry = next(e for e in import_plan if e["original_filename"] == "sprite.png")
    assert png_entry["destination_path"] == "var/assets/characters/mambo/avatar/sprite.png"
    assert png_entry["canonical_character_id"] == "matikanetannhauser"
    
    pth_entry = next(e for e in import_plan if e["original_filename"] == "matikanetannhauser_v2.pth")
    assert pth_entry["destination_path"] == "var/assets/characters/mambo/models/rvc/matikanetannhauser_v2.pth"
    
    # Check Profile Update Proposal
    profile_update = json.loads((output_dir / "profile-update-proposal.json").read_text())
    assert profile_update["canonical_character_id"] == "matikanetannhauser"
    assert profile_update["canonical_identity_status"] == "verified"
