# Voice and Speech Architecture

## Concept Boundaries

This document defines the boundaries between five distinct concepts that must
never be conflated:

| Concept | What it is | What it is NOT |
|---|---|---|
| **Voice Interaction** | The orchestration layer that callers use to request speech | An infrastructure component |
| **TTS Provider** | A concrete engine that converts text to audio | A business rule or agent |
| **Voice Profile** | Metadata describing a persona's voice characteristics | Code or configuration logic |
| **Audio Artifact** | A WAV file produced by a synthesis run | A TTS provider or playback system |
| **Playback Adapter** | A system component that plays an existing audio file | A synthesis engine |

---

## Architecture Diagram

```
Primary Agent (or CLI, or future UI)
 │
 │  SpeechRequest (text, profile, rate, volume, play_audio)
 ▼
VoiceService                                    [interaction/voice/service.py]
 │
 │  synthesize(request) → SpeechArtifact
 ▼
TtsProvider (abstract)                          [infrastructure/speech/tts/base.py]
 │
 │  (concrete implementation)
 ▼
WindowsSystemTtsProvider                        [infrastructure/speech/tts/windows_system.py]
 │
 │  Writes WAV to disk
 ▼
SpeechArtifact (path, format, provider, size)   [interaction/voice/contracts.py]
 │
 │  (if play_audio=True)
 ▼
AudioPlayer (protocol in service.py)
 │
 ▼
WindowsAudioPlayer                              [infrastructure/speech/playback/windows.py]
 │
 ▼
Windows System Audio Output (speakers)
```

---

## Module Responsibilities

### `interaction/voice/` — Voice Interaction Layer

- Defines the public contracts: `SpeechRequest`, `SpeechArtifact`, `SpeechResult`.
- Defines domain errors: `VoiceError`, `TtsProviderError`, `PlaybackError`, etc.
- `VoiceService` orchestrates: validate → synthesize → play → return result.
- **Does not** contain any PowerShell, Windows COM, or provider-specific code.
- **Does not** import MAS runtime, agents, or memory.

### `infrastructure/speech/tts/` — TTS Provider Abstraction and Implementations

- `base.py`: abstract `TtsProvider` interface. VoiceService depends on this only.
- `windows_system.py`: Windows SAPI implementation via PowerShell + System.Speech.
- Future providers (F5-TTS, GPT-SoVITS, ElevenLabs) implement `TtsProvider`.
- Swapping providers requires no changes to `VoiceService` or callers.

### `infrastructure/speech/playback/` — Audio Playback

- `windows.py`: `WindowsAudioPlayer` plays existing WAV files synchronously.
- Playback is **separate** from synthesis. The player never synthesizes.

### `infrastructure/speech/audio/` — Audio Utilities

- WAV validation (`is_valid_wav`).
- Duration extraction (`wav_duration_ms`).
- No synthesis or playback logic.

### `profiles/voices/` — Voice Profiles

- YAML or Markdown metadata files describing a persona's voice configuration.
- Contain: language, provider preference, rate defaults, voice name hints.
- **Contain no code**. No business logic.
- `profiles/voices/mambo/VOICE.md`: the Mambo placeholder profile.

---

## Data Flow — Text to Audio

```
1. Caller creates SpeechRequest(text="...", ...)
2. SpeechRequest validates itself (text non-empty, rate in range, volume in range,
   output_path inside var/)
3. VoiceService.speak(request) is called
4. VoiceService calls TtsProvider.synthesize(request)
5. WindowsSystemTtsProvider:
     a. Writes text + config to a JSON temp file (no shell interpolation)
     b. Writes PowerShell script to a temp file
     c. Calls powershell.exe -File <script> <config> (shell=False)
     d. PowerShell: loads System.Speech, selects voice, sets rate/volume,
        calls SetOutputToWaveFile + Speak
     e. Temp files are cleaned up
     f. Returns SpeechArtifact(path, size, voice_name, ...)
6. VoiceService optionally calls AudioPlayer.play(artifact.path)
7. VoiceService returns SpeechResult(artifact, played, duration_ms, warnings)
```

---

## Runtime Data Locations

| Data | Location | Committed to Git |
|---|---|---|
| Generated WAV files | `var/artifacts/audio/` | No |
| TTS cache | `var/cache/tts/` | No |
| Future TTS models | `var/models/tts/` | No |
| Voice profile metadata | `profiles/voices/` | Yes |
| Reference audio (future) | `profiles/voices/mambo/references/` | No (large binary) |

---

## Security Properties

- User text is **never** interpolated into PowerShell command strings.
  It is written to a UTF-8 JSON temp file and read by the script at runtime.
- `subprocess` is always called with `shell=False`.
- WAV output paths are validated to be inside `var/` and not inside `src/`.
- Existing output files are not overwritten unless explicitly permitted.
- All temp files are cleaned up after synthesis.
- Synthesis has a configurable timeout (default 60s).

---

## TTS Is Not an Agent

`VoiceService` and `TtsProvider` are **not agents**.

They have no identity, no task lifecycle, no private context, and no autonomy.
They are infrastructure services called by the Primary Agent (and the CLI).

They do not appear in the MAS runtime. They do not receive `AgentTask` objects.
They are invoked synchronously as part of a response pipeline.

---

## What Is Not Implemented in This Milestone

| Feature | Status |
|---|---|
| Voice cloning (F5-TTS, GPT-SoVITS, Fish Speech) | Not implemented |
| Speech-to-text (STT / microphone) | Not implemented |
| Wake word / always-on listening | Not implemented |
| Streaming / interruptible playback | Not implemented |
| ElevenLabs / Cartesia cloud TTS | Not implemented |
| Avatar lip sync | Not implemented |
| MAS runtime integration | Not implemented |
| Primary Agent voice delegation | Not implemented |

The current provider (Windows System TTS) is a functional first step
that validates the architecture before real voice cloning is introduced.
