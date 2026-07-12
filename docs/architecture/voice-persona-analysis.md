# Voice Persona Analysis Architecture

## Purpose and Scope

This document defines the role of multimodal LLM analysis in the voice pipeline,
the Voice Hint schema, and the constraints on what analysis may and may not claim.

---

## What Multimodal LLM Does (and Does Not Do)

### Permitted

| Task | Description |
|---|---|
| Analyze audio reference | Describe acoustic features of a clip |
| Analyze video reference | Describe vocal delivery from video |
| Produce transcript | Convert speech to text (if model supports) |
| Describe speaking style | Rate, pitch tendency, energy, rhythm, pauses |
| Assess audio quality | Noise, music, multiple speakers, compression |
| Generate Voice Hint | Structured JSON describing style |
| Flag quality issues | Warnings about clips unsuitable for training |
| Suggest clip selection | Which clips are cleaner / more representative |

### Forbidden

| Task | Reason |
|---|---|
| Identify the speaker by name | Speaker identification is out of scope; privacy |
| Guess canonical character | Must come from source metadata, not inference |
| Create speaker embedding | Separate technical process; not LLM's job |
| Train RVC or TTS model | Training is a separate offline pipeline |
| Claim to clone a voice | Cannot be done by analysis alone |
| Return chain-of-thought | Private reasoning must not appear in output |
| Download reference files | All inputs must be locally supplied |
| Replace audio preprocessing | Analysis complements, does not replace, DSP |

---

## Analysis Pipeline

```
User supplies: local audio or video file
 │
 ▼
Media Validation
 │  - file exists?
 │  - format supported?
 │  - SHA-256 hash computed
 │
 ▼
Capability Check
 │  - does provider support audio input?
 │  - does provider support video input?
 │  - if not: fallback to transcript + metadata
 │
 ▼
Multimodal LLM Call (with structured prompt)
 │  - prompt enforces: no speaker identification
 │  - prompt requests: observed / inferred / unknown labels
 │  - prompt requests: structured JSON output
 │  - prompt requests: confidence level
 │  - prompt requests: quality warnings
 │
 ▼
Structured Voice Hint (JSON)
 │
 ▼
Stored at: var/artifacts/voice-analysis/<profile>_voice_hint.json
 │
 ▼
Voice Profile updated: profiles/characters/<profile>/voice-hint.json
```

---

## Voice Hint Schema (Key Fields)

| Field | Type | Notes |
|---|---|---|
| `profile_id` | str | Stable internal ID, e.g. 'mambo' |
| `persona_alias` | str | User-facing name |
| `canonical_character_id` | str \| None | Null until externally verified |
| `canonical_identity_status` | enum | `unresolved` until verified |
| `source_references` | list | Files analyzed (path + hash) |
| `transcript` | str \| None | Verbatim if extracted |
| `style.speaking_rate` | str | 'slow' \| 'normal' \| 'fast' \| ... |
| `style.pitch_tendency` | str | 'high' \| 'mid' \| 'low' \| ... |
| `style.energy` | str | 'calm' \| 'moderate' \| 'high energy' \| ... |
| `style.timbre_descriptors` | list[str] | Descriptive only, e.g. ['bright', 'breathy'] |
| `style.style_prompt` | str | One-sentence style summary (no speaker name) |
| `audio_quality` | list | Per-clip quality assessment |
| `overall_confidence` | enum | `high` \| `medium` \| `low` \| `insufficient_data` |
| `warnings` | list[str] | Non-fatal analysis warnings |
| `analysis_provider` | str | Which provider ran analysis |
| `analyzed_at` | datetime | UTC timestamp |
| `version` | int | Incremented on each update |

---

## Observation Status

Every style field carries an `_status` companion field:

| Value | Meaning |
|---|---|
| `directly_observed` | Clearly audible in the reference |
| `inferred` | Reasonable conclusion from the audio |
| `unknown` | Cannot be determined from this reference |

This prevents false precision in the Voice Hint.

---

## Confidence Levels

| Level | Meaning |
|---|---|
| `high` | Multiple clean clips, consistent analysis |
| `medium` | Limited clips or some quality issues |
| `low` | Poor quality, short duration, or conflicting signals |
| `insufficient_data` | Not enough reference to make any determination |

---

## Privacy and Ethical Constraints

1. The Voice Hint does NOT identify or name the speaker.
2. The Voice Hint does NOT claim to reproduce a real person's voice exactly.
3. Extracted game audio is copyrighted — see `config/external-sources/` for license status.
4. Analysis results are stored locally only — not transmitted externally.
5. Chain-of-thought (internal model reasoning) is never stored or logged.

---

## Windows TTS Mapping Limitations

When Windows System TTS is the active provider, only a small subset of the
Voice Hint can be applied:

| Hint Field | Windows TTS Mapping | Supported |
|---|---|---|
| `speaking_rate` | SAPI Rate (-10 to +10) | ✅ Partial |
| `energy` | Volume (0–100) | ✅ Partial |
| `timbre_descriptors` | (none) | ❌ |
| `pitch_tendency` | (none) | ❌ |
| `rhythm` | (none) | ❌ |
| `pause_style` | (none) | ❌ |
| `expressiveness` | (none) | ❌ |
| `emotional_tone` | (none) | ❌ |
| `conversational_attitude` | (none) | ❌ |
| `pronunciation_notes` | (none) | ❌ |
| `character_identity` | (none) | ❌ |

**Output label when using Windows TTS with Voice Hints:**  
*"Beta default system voice — styled with available Windows hints."*  
**NOT:** "Mambo cloned voice" or "character voice."

---

## Profile Versioning

Each update to a Voice Hint increments its `version` field.
Previous versions should be archived in `var/assets/characters/<profile>/metadata/`.
The most recent version in `profiles/characters/<profile>/voice-hint.json` is authoritative.
