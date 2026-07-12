# Local Character Asset Inspection Guide

This guide explains how to use the read-only CLI tool to scan local character assets (avatars, audio, models) and generate an import proposal for Beta.

## Core Principles
- **Read-Only**: The inspection tool will **never** modify, copy, or upload your original files. It only scans them to generate JSON reports.
- **Security First**: Executables, DLLs, and symlinks escaping the directory are blocked. RVC models (`.pth`) are hashed but **not** loaded into memory by the scanner.
- **Identity Resolution**: Beta will try to determine the canonical character ID (e.g., `matikanetannhauser`) from the folders and metadata you provide, rather than just assuming it matches your persona alias (e.g., `mambo`).

---

## 1. Prepare Your Local Sources

You need to have your assets extracted locally. Beta does not download copyrighted files for you.

Examples of sources you might have:
- **Desktop Gremlin Package**: `C:\Users\You\Downloads\Desktop_Gremlin`
- **Voice Extractor Output**: `C:\Users\You\Downloads\umamusume-voice-text-extractor\output`
- **RVC Model Directory**: `C:\Users\You\Downloads\RVC-Umamusume\matikanetannhauser`

---

## 2. Run the Inspection CLI

Run the `inspect_character_assets.py` script and pass the paths to the sources you want to inspect. You must provide your alias using `--profile` and at least one local source.

```powershell
# Make sure your virtual environment is active
.\.venv\Scripts\Activate.ps1

python apps/cli/inspect_character_assets.py `
  --profile mambo `
  --desktop-gremlin "C:\Users\You\Downloads\Desktop_Gremlin" `
  --voice-dataset "C:\Users\You\Downloads\umamusume-voice-text-extractor\output" `
  --rvc-model "C:\Users\You\Downloads\RVC-Umamusume\matikanetannhauser"
```

### Available Options:
- `--profile`: **Required**. Your persona alias (e.g., `mambo`).
- `--desktop-gremlin`: Path to Desktop Gremlin or Tracen Academy package (finds avatars).
- `--game-data`: Path to UmaViewer or raw game data.
- `--voice-dataset`: Path to voice clips and transcripts.
- `--rvc-model`: Path to RVC models (`.pth`, `.index`).

---

## 3. Review the Output

If the scan is successful, Beta will generate reports in:
`var/artifacts/character-inspection/<profile>/`

You should review the following files before proceeding with an actual import:

1. **`inspection-summary.json`**: Shows the total assets found, the resolved identity status, and Beta's recommendation for the best Voice Pipeline (e.g., "Base TTS -> RVC").
2. **`identity-evidence.json`**: Shows the evidence Beta found to resolve the canonical character ID. If it says `conflicting` or `unresolved`, you may not have provided enough metadata.
3. **`import-plan.json`**: A proposed list of all files that Beta wants to copy into its internal `var/assets/` directory in the next step.
4. **`profile-update-proposal.json`**: Proposed updates to `profiles/characters/<profile>/CHARACTER.md`.
5. **`warnings.md`**: Any security warnings (e.g., skipped executables, files too large).

---

## 4. Next Steps

Once you are satisfied with the `import-plan.json` and the identity resolution, you will be able to instruct Beta to execute the import in the next milestone.

**(Note: Execution of the import plan is not yet implemented. This milestone only generates the proposal.)**
