# Mambo Voice Profile

**Profile ID:** mambo  
**Display Name:** Mambo  
**Status:** Placeholder system voice — voice cloning NOT implemented

---

## Current Configuration

| Field | Value |
|---|---|
| Default language | vi-VN |
| Current provider | windows-system |
| Preferred voice name | *(auto-select — use best available SAPI voice)* |
| Default rate | 0 (normal) |
| Default volume | 100 |

---

## Important Notices

**This is not a cloned voice.**

The current provider is Windows System TTS (SAPI). The voice used is whatever
Vietnamese or default voice is installed on the system. It does not replicate
any specific speaker.

The Mambo voice profile is a placeholder that will be replaced in a later
milestone when a real voice model is cloned or trained.

---

## Future Voice Cloning

When voice cloning is implemented:

- Reference audio samples will be added to `profiles/voices/mambo/references/`.
- The trained model will be stored in `var/models/tts/mambo/`.
- The provider will change from `windows-system` to the cloning engine (F5-TTS,
  GPT-SoVITS, Fish Speech, etc.).
- This profile file will be updated to reflect the new provider and model path.

**Do not add copyrighted audio to this repository.**  
**Do not auto-download model weights from this profile.**

---

## Reference Samples

*(None yet. To be added when voice cloning milestone begins.)*

Place reference WAV files in `profiles/voices/mambo/references/` when available.
