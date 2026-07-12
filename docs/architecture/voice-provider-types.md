# Voice Provider Types

## Overview

Beta supports multiple categories of voice providers. Each category has a
distinct input/output contract and must not be conflated with the others.

---

## Provider Type Matrix

| Type | Input | Output | Interface | Status |
|---|---|---|---|---|
| System TTS | Text | Audio | `TtsProvider` | ✅ Implemented (Windows) |
| Direct Character TTS | Text | Character-like audio | `TtsProvider` | ⏳ Future |
| Zero-shot TTS | Text + voice reference | Audio in reference style | `TtsProvider` | ⏳ Future |
| Fine-tuned TTS | Text | Audio (model baked) | `TtsProvider` | ⏳ Future |
| Voice Conversion / RVC | Source audio | Converted audio | `VoiceConversionProvider` | ⏳ Future |
| Voice Style Hint | — | Metadata only | `VoiceHint` (contract) | ✅ Schema defined |
| Speaker Embedding | Audio | Vector embedding | Separate module | ⏳ Future |

---

## 1. System TTS

**Interface:** `TtsProvider`  
**Input:** Text  
**Output:** WAV audio (system default voice)  
**Current implementation:** `WindowsSystemTtsProvider` (Windows SAPI)

Characteristics:
- No character identity.
- No voice cloning.
- No model training.
- Requires only the OS TTS engine.
- Voice can be selected from installed SAPI voices.
- Rate and volume can be adjusted via Voice Hint mapping.

**Output label:** *Beta default system voice.*  
**NOT:** Character voice.

---

## 2. Direct Character TTS

**Interface:** `TtsProvider`  
**Input:** Text + optional style hints  
**Output:** Character-like audio directly

Examples of future providers:
- GPT-SoVITS (with character-specific fine-tuning)
- F5-TTS (with character reference audio)
- Fish Speech
- ElevenLabs (cloud)
- Cartesia (cloud)

Characteristics:
- Model is trained on or conditioned by character voice.
- No separate voice conversion step needed.
- Requires character-specific model or configuration.
- Implements the same `TtsProvider` interface — transparent to VoiceService.

---

## 3. Zero-shot TTS

**Interface:** `TtsProvider`  
**Input:** Text + voice reference audio (prompt)  
**Output:** Audio in the style of the reference

Examples:
- F5-TTS (zero-shot mode)
- Kokoro (with reference)

Characteristics:
- Does not require character-specific training.
- Quality depends heavily on reference audio quality.
- Reference must be clean, solo-speaker audio.
- Still implements `TtsProvider` — reference is part of request parameters.

---

## 4. Fine-tuned TTS

**Interface:** `TtsProvider`  
**Input:** Text  
**Output:** Audio (voice baked into model weights)

Examples:
- GPT-SoVITS after fine-tuning on character dataset.
- F5-TTS after training on character dataset.

Characteristics:
- Requires a training dataset (transcribed audio clips).
- Training is an offline process, not part of the runtime pipeline.
- The trained model is stored in `var/assets/characters/<id>/models/tts/`.
- Inference is the same as Direct Character TTS from the interface perspective.

---

## 5. Voice Conversion / RVC

**Interface:** `VoiceConversionProvider`  
**Input:** Source audio (WAV from any TtsProvider)  
**Output:** Converted WAV (source content, target timbre)

**CRITICAL: This is NOT a TtsProvider.**  
It does not accept text. It requires audio as input.

Pipeline:
```
Text
 └─ TtsProvider (System TTS or any base TTS)
      └─ source audio
           └─ VoiceConversionProvider (RVC)
                └─ character-like audio
```

Examples:
- RVC v2 (Retrieval-based Voice Conversion)
- SoVITS-SVC

Characteristics:
- Requires a model file (`.pth`) and feature index (`.index`).
- Model must be trained on or for the target character.
- Separate `VoiceConversionProvider` interface (see `voice_conversion_base.py`).
- The pipeline result approximates character timbre, not exact voice.

---

## 6. Voice Style Hint

**Interface:** `VoiceHint` (data contract, not a provider)  
**Input:** — (produced by multimodal analysis)  
**Output:** Structured metadata about speaking style

Voice Hints are:
- Provider-neutral.
- Not a model or embedding.
- Not executable — they are descriptive metadata.
- Used to configure a provider (within its capability limits).

See `docs/architecture/voice-persona-analysis.md` for the full schema.

---

## 7. Speaker Embedding

**Interface:** Separate module (not yet defined)  
**Input:** Audio clip  
**Output:** Vector representation of the speaker's voice

Speaker embeddings are used by some voice models for speaker conditioning.

Characteristics:
- Not a TTS provider.
- Not a Voice Conversion provider.
- Produced offline from reference audio.
- Stored in `var/assets/characters/<id>/models/embeddings/`.
- Not to be confused with Voice Hints (which are textual metadata).

---

## Interface Summary

```python
# TtsProvider: text → audio
class TtsProvider(ABC):
    def synthesize(self, request: SpeechRequest) -> SpeechArtifact: ...
    def list_voices(self) -> list[VoiceInfo]: ...
    def health_check(self) -> None: ...

# VoiceConversionProvider: audio → audio
class VoiceConversionProvider(ABC):
    def convert(self, request: VoiceConversionRequest) -> VoiceConversionArtifact: ...
    def load_model(self, model_info: VoiceConversionModelInfo) -> None: ...
    def health_check(self) -> None: ...

# VoiceHint: metadata only (not a provider)
# Produced by: VoiceHintAnalyzer.analyze(reference_path, ...)
# Stored at: profiles/characters/<profile>/voice-hint.json
```

---

## Terminology Rules

Never use the term **"voice model"** without specifying the type.

Use instead:
- RVC voice conversion model
- Direct character TTS model
- Zero-shot TTS reference audio
- Fine-tuned TTS model
- Speaker embedding
- Voice Style Hint

These are distinct concepts with distinct data formats, interfaces, and pipelines.
