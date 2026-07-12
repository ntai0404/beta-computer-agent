# Mambo — Character Profile

**Profile ID:** `mambo`  
**Display Alias:** Mambo  
**Canonical Character:** ⚠️ UNRESOLVED  
**Canonical Character ID:** ⚠️ UNRESOLVED  
**Source Status:** Pending verification  

---

> [!IMPORTANT]
> This profile does NOT represent a verified canonical character.
> "Mambo" is a user-facing persona alias only.
> Canonical identity, sprite, model, and voice references must be sourced
> and verified before this profile is updated.

---

## Current Status

| Field | Status |
|---|---|
| Canonical character name | **Unresolved** |
| Canonical character ID | **Unresolved** |
| Source package | **Pending verification** |
| Avatar asset | **Not imported** |
| Voice references | **Not imported** |
| Transcripts | **Not imported** |
| Voice Hint | **Pending analysis** |
| Voice conversion model (RVC) | **Not available** |
| Direct TTS model | **Not available** |
| Speaker embedding | **Not available** |
| Active TTS provider | `windows-system` (system default — NOT a character voice) |

---

## Persona Alias

The alias `mambo` is the name the user uses to refer to this character within Beta.
This alias is stable across sessions, regardless of whether canonical identity is resolved.

**Alias ≠ Canonical character ID.**

When canonical identity is confirmed:
- Update `canonical_character` and `canonical_character_id` fields here.
- Do NOT change the profile ID `mambo` — it is the stable internal reference.
- Do NOT change the display alias unless the user explicitly requests it.

---

## Asset Import Locations

All large assets are placed outside `profiles/` and outside `src/`.

| Asset Type | Location |
|---|---|
| Avatar sprites / models | `var/assets/characters/mambo/avatar/` |
| Voice reference audio | `var/assets/characters/mambo/references/audio/` |
| Voice reference video | `var/assets/characters/mambo/references/video/` |
| Transcripts | `var/assets/characters/mambo/transcripts/` |
| Training datasets | `var/assets/characters/mambo/datasets/` |
| RVC voice conversion model | `var/assets/characters/mambo/models/rvc/` |
| Direct TTS model | `var/assets/characters/mambo/models/tts/` |
| Speaker embeddings | `var/assets/characters/mambo/models/embeddings/` |
| Asset metadata | `var/assets/characters/mambo/metadata/` |
| Generated audio | `var/artifacts/audio/` |
| Voice analysis results | `var/artifacts/voice-analysis/` |

These paths are excluded from Git. See `.gitignore`.

---

## Sources to Verify

See `sources.md` for the list of external sources that must be examined
to resolve canonical identity and populate this profile.

---

## Current Voice Warning

The active voice provider (`windows-system`) produces Windows system voice audio.

> **This is NOT a cloned or synthesized character voice.**
> Output is labeled as: *Beta default system voice — styled with available hints.*

Voice Hint mapping for Windows System TTS is limited to:
- `speaking_rate` → SAPI Rate
- `energy` → Volume
- Installed voice preference → SelectVoice (if available)

Character timbre, emotional nuance, exact pitch contour, and expressive prosody
are NOT reproducible with Windows System TTS.

---

## Update History

| Date | Change | Author |
|---|---|---|
| 2026-07 | Initial placeholder created | beta-setup |
