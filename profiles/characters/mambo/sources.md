# Mambo — External Sources

This document lists the external sources that must be examined to resolve
the canonical identity of the `mambo` character profile.

**Current canonical identity status: UNRESOLVED**

No source has been verified yet. No assets have been imported.

---

## Sources to Verify

### 1. Desktop_Gremlin / Tracen Academy Package

**Purpose:** Identify the real mascot/character packaged in this application.

| Field | Status |
|---|---|
| Source type | Desktop application / package |
| Expected assets | Sprite sheets, animation files, desktop character model, possible audio |
| Canonical character name | Unknown — must be read from package metadata |
| Canonical character ID | Unknown |
| Import status | **Not started** |
| License status | **Not verified** |
| User-supplied path | *(not provided yet)* |
| Last verified | Never |

**Required actions before import:**
1. User provides local path to the installed or extracted package.
2. Inspect package metadata for character name/ID.
3. Identify sprite and animation formats.
4. Identify audio format if present.
5. Verify license terms for personal AI assistant use.
6. Update this file with findings.

**Public upstream evidence checked:**
- Canonical repository checked: `https://github.com/KurtVelasco/Desktop_Gremlin`
- Branch checked: `tracen` at `feed8f6d87d8745d58c84e2a83cfa244314bdf21`
- Actual release tag checked: `v4.0`, release name `TracenAcademy_v4.0`
- Requested tag URL `/releases/tag/TracenAcademy_v4.0` returned 404 after redirect.
- README lists `Matikanetannhauser` v2.7.2 with package `Mambo_v2.8.zip`.
- Source mapping found for sprite actions/emotes and `Sounds/<character>/<file>.wav`.

This evidence does not verify the local `mambo` profile and does not provide a
usable local voice reference.

---

### 2. UmaViewer or Equivalent Uma Musume Asset Reader

**Purpose:** Inspect character model, animation, facial animation, and voice metadata.

| Field | Status |
|---|---|
| Source type | Game asset viewer / reader tool |
| Expected assets | 3D model, animations, facial rig, metadata |
| Asset origin | Uma Musume Pretty Derby |
| Canonical character name | Unknown — must be identified from in-game ID |
| Canonical character ID | Unknown |
| Import status | **Not started** |
| License status | **Not verified — game assets may not be freely redistributable** |
| User-supplied path | *(not provided yet)* |
| Last verified | Never |

**Warnings:**
- Game assets are owned by Cygames / DMM. Verify redistribution rights before use.
- This tool reads assets; it does not grant permission to use them.
- Do NOT commit extracted game assets to Git.

---

### 3. umamusume-voice-text-extractor or Equivalent

**Purpose:** Extract voice audio clips and associated transcripts.

| Field | Status |
|---|---|
| Source type | Voice/text extraction tool for Uma Musume |
| Expected assets | WAV/OGG audio clips, transcript text, character IDs, scene metadata |
| Asset origin | Uma Musume Pretty Derby game data |
| Canonical character ID | Unknown — must match extracted metadata |
| Import status | **Not started** |
| License status | **Not verified — extracted audio is copyrighted** |
| User-supplied path | *(not provided yet)* |
| Last verified | Never |

**Warnings:**
- Extracted audio files are copyrighted by Cygames.
- Do NOT commit extracted audio to Git.
- Do NOT redistribute.
- Use only for personal, non-commercial voice analysis under applicable fair use.
- Consult applicable law before proceeding.

---

### 4. RVC-Umamusume or Equivalent Voice Conversion Model Repository

**Purpose:** Check for a voice conversion (RVC) model trained on the target character.

| Field | Status |
|---|---|
| Source type | RVC model repository |
| Expected assets | `.pth` model weights, `index` files |
| Model format | RVC v2 (or equivalent) |
| Sample rate | Unknown — must be read from model |
| Target character | Unknown — must match canonical character ID |
| Import status | **Not started** |
| License status | **Not verified** |
| User-supplied path | *(not provided yet)* |
| Last verified | Never |

**Important distinctions:**
- RVC is a Voice Conversion model, NOT a Text-to-Speech model.
- RVC pipeline: `text → Base TTS → source audio → RVC → character-like audio`
- Direct TTS pipeline: `text → Character TTS model → character-like audio`
- These are different providers with different interfaces.

---

## Next Steps

1. User supplies local paths or download instructions for each source.
2. The import boundary (`src/beta/infrastructure/character_assets/`) validates each source.
3. Validated assets are placed in `var/assets/characters/mambo/` (not committed to Git).
4. Voice references are submitted to multimodal voice analysis.
5. Voice Hint is generated and stored in `profiles/characters/mambo/`.
6. Canonical identity is confirmed and this file is updated.
