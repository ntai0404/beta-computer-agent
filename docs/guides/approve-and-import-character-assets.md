# Approving and Importing Character Assets

This guide explains how to use the `import_character_assets.py` script to safely import character assets into Beta's internal storage (`var/assets/characters/`) after you have successfully run the inspection tool.

Beta enforces an **Explicit Approval** policy. It will never automatically import all files discovered during the inspection phase. You must explicitly tell Beta which files are approved for import.

## Prerequisites

1. You must have already run the `inspect_character_assets.py` CLI.
2. The `var/artifacts/character-inspection/<profile>/import-plan.json` must exist.
3. You should review the inspection summary and identity evidence to ensure they look correct.

---

## 1. Creating the Approval List

You have two ways to approve assets: via CLI flags or via an approval JSON file.

### Option A: Using CLI Flags
You can approve individual files by passing their original filename to the `--approve-id` flag. This is useful for small imports.
```powershell
--approve-id sprite.png --approve-id model.pth
```

### Option B: Using an Approval JSON File
For larger imports, it is easier to create an `approved-assets.json` file.

**`approved-assets.json`**
```json
{
  "profile_id": "mambo",
  "inspection_id": "latest",
  "approved_asset_ids": [
    "sprite.png",
    "clip1.wav",
    "metadata.json",
    "mambo_v2.pth"
  ],
  "apply_profile_update": true,
  "approved_by": "user",
  "notes": "Approved after manual review"
}
```

If `"apply_profile_update": true` is set, Beta will automatically apply the `profile-update-proposal.json` to your `CHARACTER.md` file (if the identity was verified).

---

## 2. Dry Run (Recommended)

Before actually copying files, perform a dry run. The dry run will validate the checksums, paths, and conflicts without touching your `var/assets/` directory.

```powershell
python apps/cli/import_character_assets.py `
  --profile mambo `
  --plan "var/artifacts/character-inspection/mambo/import-plan.json" `
  --approve-file "C:\path\to\approved-assets.json" `
  --dry-run
```

Review the CLI output and check `var/artifacts/character-import/mambo/dry-run-import-summary.json`.

---

## 3. Execute the Import

Once you are satisfied with the dry run, run the script without the `--dry-run` flag:

```powershell
python apps/cli/import_character_assets.py `
  --profile mambo `
  --plan "var/artifacts/character-inspection/mambo/import-plan.json" `
  --approve-file "C:\path\to\approved-assets.json"
```

If you don't use the approval JSON file to set the profile update flag, you can pass it via CLI:
```powershell
python apps/cli/import_character_assets.py --profile mambo --plan ... --approve-id sprite.png --apply-profile-update
```

### What Beta Does During Import:
1. Re-validates the source file's existence and checksum against the inspection plan.
2. Checks the destination in `var/assets/characters/<profile>/`. If it exists with a matching checksum, it's marked as `already_present`. If it has a different checksum, it's marked as `conflict` and blocked.
3. Copies the file atomically using a `.tmp_import` extension, then re-verifies the checksum of the copy, and renames it to the final filename.
4. Updates `CHARACTER.md` if `--apply-profile-update` is true.
5. Writes a provenance manifest to `var/assets/characters/<profile>/metadata/import-manifest_*.json`.
6. Writes a rollback manifest to `var/artifacts/character-import/<profile>/rollback-manifest.json`.

---

## 4. Rollback

If you made a mistake or want to revert an import batch, use the `--rollback` flag.

The rollback process safely removes only the files created during that specific import batch. It verifies that the checksums have not changed before deleting the files to ensure it doesn't delete files you manually modified after the import.

```powershell
python apps/cli/import_character_assets.py `
  --profile mambo `
  --rollback "var/artifacts/character-import/mambo/rollback-manifest.json"
```

> **Note**: Rollback does NOT revert updates made to `CHARACTER.md`. If you need to revert the profile metadata, restore it from `var/artifacts/character-import/mambo/backups/`.

---

## 5. Security Notes

- **Executables and Symlink Escapes**: The tool will actively block and fail attempts to copy executable files or symlinks pointing outside the profile's asset root.
- **Model Files**: RVC models (`.pth`, `.index`) and other model weights are treated as opaque binaries. Beta does **not** load or execute them during the import process. Their status in the manifest is recorded as `imported_untrusted_not_loaded`.
