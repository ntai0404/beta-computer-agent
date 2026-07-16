# Character Voice Pipeline

This document explains the possible voice pipelines that Beta can execute to give life to a character.

## Pipeline Options

### 1. Windows System TTS Fallback (`system_tts`)
- **Status:** **Active**
- **Flow:** Text -> `WindowsSystemTtsProvider` -> WAV -> Playback
- **Description:** Uses the built-in Windows voices (SAPI5). It supports basic rate and volume hints. When invoked for a character like `mambo`, it produces a visible warning that this is *not* a cloned voice.

### 2. Base TTS + Voice Conversion (`base_tts_plus_conversion`)
- **Status:** *Planned (Foundation Ready)*
- **Flow:** Text -> Base TTS (e.g., F5-TTS) -> Intermediate WAV -> `VoiceConversionProvider` (e.g., RVC) -> Final WAV -> Playback
- **Description:** Generates natural intonation using a high-quality base TTS, then converts the vocal timbre to the character's voice using an RVC model. Currently, imported RVC models are detected but marked as `untrusted_not_loaded`, blocking this pipeline.

### 3. Direct Character TTS (`direct_character_tts`)
- **Status:** *Planned*
- **Flow:** Text -> `CharacterTtsProvider` -> WAV -> Playback
- **Description:** Uses an end-to-end character TTS model (e.g., GPT-SoVITS or a specific ElevenLabs voice ID) to directly generate the character's voice.

## Profile Readiness Status

The pipeline selector bases its decision on the `ReadinessStatus` derived from the character's imported assets:
- `FALLBACK_READY`: No assets found. Uses `system_tts`.
- `BLOCKED`: Assets found (e.g., RVC model), but they lack explicit trust authorization. Uses `system_tts`.
- `CONVERSION_READY`: Trusted RVC model available. Uses `base_tts_plus_conversion`.
- `DIRECT_TTS_READY`: Trusted end-to-end model available. Uses `direct_character_tts`.

## Voice Hints

A `VoiceHint` contains structured emotional or stylistic metadata (like `speaking_rate` and `volume`). It maps these abstract values down to the specific provider capabilities. For example, a `1.5` speaking rate is translated into SAPI5's internal `1` to `10` rate scale by the `WindowsSystemTtsProvider`. In the future, this hint will be generated dynamically by a `VoiceHintAnalyzer` reading from multi-modal inputs.

## Real Voice I/O Contracts

### Voice Hint Analysis

**Input:** A local audio/video reference, optional existing transcript, profile
metadata, and source provenance. No URL downloads. No cloud upload unless the
user explicitly approves a cloud provider call.

**Output:** VoiceHint metadata, confidence, warnings, source checksums, and
quality notes. It is not audio, not a speaker embedding, and not proof of
canonical identity.

### Base TTS

**Input:** Text plus only the subset of VoiceHint fields supported by the active
TTS provider.

**Output:** A source WAV file. With `windows-system`, this is the OS voice only.
It must not be labeled as Mambo voice.

### RVC Conversion

**Input:** Source WAV audio plus a trusted RVC voice conversion model.

**Output:** Converted WAV audio. Current milestone is discovery only:
RVC models are not loaded, not executed, and not trusted automatically.

### Final Voice Pipeline

**Input:** `SpeechRequest(text, character_profile_id, pipeline_preference, ...)`.

**Output:** `SpeechArtifact` WAV, warnings, and pipeline trace. Current output is
`Beta default system voice` unless a real character provider/model is approved
and run. It is not character matched in the current pipeline.
