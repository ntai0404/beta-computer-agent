# External Source: RVC / Voice Conversion Models

**Source name:** RVC-Umamusume or equivalent voice conversion model repository  
**Purpose:** Check for a voice conversion model trained on the target character  
**Import status:** NOT STARTED  

---

## Purpose

Use this source to:

- Determine if a pre-trained RVC model exists for the target character.
- Confirm the model is trained on the correct canonical character ID.
- Identify model format, sample rate, and runtime requirements.
- Review license and usage restrictions.
- Place the model in `var/assets/characters/mambo/models/rvc/` if approved.

---

## CRITICAL DISTINCTION — RVC vs. TTS

RVC (Retrieval-based Voice Conversion) is NOT a Text-to-Speech model.

| Property | RVC | TTS |
|---|---|---|
| Input | Audio (from Base TTS or microphone) | Text |
| Output | Converted audio (same content, different timbre) | Synthesized audio |
| Pipeline role | Post-TTS conversion step | Synthesis step |

**RVC pipeline:**
```
Text → Base TTS → source audio → RVC model → character-like audio
```

**Direct Character TTS pipeline:**
```
Text → Character TTS model → character-like audio
```

These require separate provider interfaces. Do NOT merge them into one.

---

## Expected Asset Types

| Asset Type | Expected Format | Notes |
|---|---|---|
| RVC model weights | `.pth` file | PyTorch checkpoint |
| Feature index | `.index` file | Required by RVC runtime |
| Model metadata | JSON or README | Sample rate, training info |

---

## Upstream Location

| Field | Value |
|---|---|
| Tool/repo name | RVC-Umamusume (or equivalent) |
| Repository | *(to be supplied by user)* |
| Target character | *(unknown — must match canonical character ID)* |
| User-supplied model path | `var/assets/characters/mambo/models/rvc/` (after verification) |

---

## Import Status

| Step | Status |
|---|---|
| Repository identified | ⬜ Not done |
| Model for target character found | ⬜ Not done |
| Canonical character ID confirmed | ⬜ Not done |
| Model format verified | ⬜ Not done |
| Sample rate documented | ⬜ Not done |
| Runtime requirements documented | ⬜ Not done |
| License verified | ⬜ Not done |
| Model placed in var/assets/ | ⬜ Not done |
| VoiceConversionProvider implemented | ⬜ Not done |

---

## License Status

**Not verified.**

Community-trained RVC models may have:
- Restrictions on commercial use.
- Restrictions on redistribution.
- Dependency on copyrighted training data.

Review the specific model's license before use.

---

## Runtime Requirements (Unknown)

When the model is identified, document:
- Required Python packages (e.g. `faiss`, `torch`, RVC inference code).
- Required sample rate (model input and output).
- GPU requirements (if any).
- Inference latency on target hardware.

---

## Warnings

- Do NOT commit model files to Git (large binary files).
- Do NOT assume a model is trained on the correct character without verification.
- Do NOT use RVC as a TTS provider — it requires audio input, not text.
- RVC does not reproduce exact voice — it approximates timbre from the model.

---

## Last Verified

Never.
