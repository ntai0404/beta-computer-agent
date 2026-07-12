# External Source: Uma Musume Voice Dataset

**Source name:** umamusume-voice-text-extractor (or equivalent)  
**Purpose:** Extract voice audio clips and transcripts from game data  
**Import status:** NOT STARTED  

---

## Purpose

Use this tool to:

- Extract individual voice audio clips for the target character.
- Obtain matching transcript text for each clip.
- Obtain character IDs and scene/event metadata.
- Identify clip quality, duration, and conditions.
- Prepare a dataset of clean, transcribed audio clips.

These clips become the Voice Reference set for multimodal analysis and,
eventually, voice model training.

---

## Expected Asset Types

| Asset Type | Expected Format | Notes |
|---|---|---|
| Voice audio clips | WAV, OGG, or ACB | Per-character, per-scene |
| Transcripts | TXT or JSON | Japanese, possibly multilingual |
| Character ID mapping | JSON | Maps clip to character |
| Scene/event metadata | JSON | Category, emotional context |

---

## Upstream Location

| Field | Value |
|---|---|
| Tool name | umamusume-voice-text-extractor (or equivalent) |
| Repository | *(to be supplied by user)* |
| Asset origin | Uma Musume Pretty Derby game data (Cygames / DMM) |
| User-supplied game data path | *(not provided)* |
| User-supplied output path | `var/assets/characters/mambo/references/audio/` (after character confirmation) |

---

## Import Status

| Step | Status |
|---|---|
| Tool installed | ⬜ Not done |
| Game data path supplied | ⬜ Not done |
| Target character ID confirmed | ⬜ Not done |
| Clips extracted | ⬜ Not done |
| Transcripts extracted | ⬜ Not done |
| Audio placed in var/assets/ | ⬜ Not done |
| Transcripts placed in var/assets/ | ⬜ Not done |
| Clip quality reviewed | ⬜ Not done |
| Dataset prepared | ⬜ Not done |

---

## License Status

**Not verified.**

Extracted audio is copyrighted by Cygames / DMM.
Personal use for voice analysis may or may not be permitted under applicable law.

Conditions:
- Do NOT commit extracted audio to Git.
- Do NOT redistribute.
- Do NOT use for commercial purposes.
- Consult applicable copyright law before proceeding.

---

## Dataset Quality Notes

Before submitting to voice analysis, each clip should be screened for:

- Background music (presence/absence).
- Multiple speakers (solo vs. overlapping).
- Sound effects over voice.
- Compression artifacts.
- Clip duration (minimum for training varies by model).
- Transcript accuracy.

The multimodal voice analyzer provides structured quality assessment for each clip.

---

## Warnings

- Do NOT extract audio until canonical character ID is confirmed.
- Do NOT assume all extracted clips contain only the target character.
- Do NOT commit audio to Git under any circumstances.

---

## Last Verified

Never.
