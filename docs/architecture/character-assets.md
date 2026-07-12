# Character Assets Architecture

## Core Principle

Beta never assumes an external asset exists. All character assets must be:

1. Supplied by the user from a local path.
2. Validated by the import boundary.
3. Placed in `var/assets/characters/<profile_id>/` (not committed to Git).
4. Documented in `profiles/characters/<profile_id>/` (committed to Git).

---

## Concept Map

```
Persona Alias (user-facing name, e.g. "Mambo")
 └─ Character Profile (profiles/characters/mambo/)
      ├─ CHARACTER.md          — status, warnings, asset locations
      ├─ sources.md            — external sources to verify
      └─ voice-hint.json       — produced after multimodal analysis (optional)

External Sources (NOT in repo)
 ├─ Desktop_Gremlin / Tracen Academy package
 ├─ Uma Musume asset viewer
 ├─ Uma Musume voice extractor
 └─ RVC / TTS model repositories

Import Boundary (src/beta/infrastructure/character_assets/)
 └─ Validates, hashes, and places assets in var/assets/

Runtime Assets (var/assets/characters/mambo/) — NOT committed
 ├─ avatar/                    — sprite / model files
 ├─ references/audio/          — voice reference WAV clips
 ├─ references/video/          — voice reference video clips
 ├─ transcripts/               — transcript text
 ├─ datasets/                  — processed training data
 ├─ models/rvc/                — RVC voice conversion model
 ├─ models/tts/                — direct TTS model (future)
 ├─ models/embeddings/         — speaker embeddings
 └─ metadata/                  — per-asset metadata JSON
```

---

## External Source Boundary

All external data enters the system through the import boundary.

**What the import boundary does:**
- Reads from a user-supplied local path.
- Validates file type and integrity (hash).
- Identifies asset category (avatar, audio, video, model).
- Copies or links to the correct `var/assets/` subdirectory.
- Writes metadata JSON (hash, source, timestamp, format).
- Does NOT download from the Internet.
- Does NOT scrape or bypass DRM.
- Does NOT commit assets to Git.

**What the import boundary does NOT do:**
- Determine canonical character identity.
- Accept URLs.
- Assume license.
- Import without user approval.

---

## Canonical Identity Resolution

Canonical character identity must be read from external source metadata —
never assumed or inferred from the persona alias.

Steps to resolve canonical identity:

1. User supplies local path to the source package (Desktop_Gremlin, game data, etc.).
2. Import boundary inspects package metadata for character name and ID.
3. If found: update `CHARACTER.md` `canonical_character` and `canonical_character_id`.
4. If not found: character remains `unresolved`. No assets are mislabeled.

**The persona alias (`mambo`) is NEVER changed automatically.**
The alias is the user's name for the character, independent of canonical identity.

---

## Avatar Import

Avatar assets (sprite sheets, Live2D models, 3D models) are placed in:

```
var/assets/characters/mambo/avatar/
```

Requirements before import:
- License reviewed and recorded in `sources.md`.
- Format identified and documented.
- Runtime library requirements documented.
- Assets do NOT enter `src/` or `profiles/`.

---

## Voice Reference Import

Voice reference audio/video clips are placed in:

```
var/assets/characters/mambo/references/audio/
var/assets/characters/mambo/references/video/
```

Requirements before import:
- Canonical character ID confirmed (clips must belong to the target character).
- License reviewed (extracted game audio is typically copyrighted).
- Quality screening: no heavy background music, no multiple speakers if possible.
- SHA-256 hash computed and stored in metadata.

Voice references are NEVER committed to Git.

---

## Voice Model Import

| Model Type | Location |
|---|---|
| RVC voice conversion model | `var/assets/characters/mambo/models/rvc/` |
| Direct TTS model | `var/assets/characters/mambo/models/tts/` |
| Speaker embeddings | `var/assets/characters/mambo/models/embeddings/` |

Requirements before import:
- License reviewed and recorded.
- Model format and sample rate documented.
- Runtime requirements documented.
- Model NOT committed to Git (large binary).

---

## Licensing Responsibility

Beta does not grant any license to use external assets.
The user is solely responsible for ensuring they have the right to use
any asset imported into `var/assets/`. See `config/external-sources/` for
per-source license status.

---

## What Is NOT in This Architecture

- Avatar rendering engine (not in this milestone).
- Lip sync runtime (not in this milestone).
- Voice cloning pipeline (not in this milestone).
- STT / microphone input (not in this milestone).
- MAS agent integration (not in this milestone).
