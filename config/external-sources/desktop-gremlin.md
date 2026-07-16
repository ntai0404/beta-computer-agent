# External Source: Desktop_Gremlin / Tracen Academy

## Scope

This is a read-only provenance record. Beta did not import, copy, extract, run,
or use any upstream asset. The temporary shallow clone and byte-range ZIP
fragments are not user-supplied local character assets and do not count as
usable Beta voice references.

## Repository And Release Evidence

| Field | Evidence |
|---|---|
| Supplied repository URL | `https://github.com/KurtVelasco/Desktop_Gremlin` |
| Live canonical endpoint checked | The supplied URL returned HTTP `301` to `https://github.com/Kritzkingvoid/Desktop_Gremlin` on 2026-07-16. GitHub API reported `full_name: Kritzkingvoid/Desktop_Gremlin`. |
| Branch | `tracen` |
| Branch commit | `feed8f6d87d8745d58c84e2a83cfa244314bdf21`, from `git ls-remote` against both URLs |
| Tracen Academy release | tag `v4.0`, release name `TracenAcademy_v4.0`, target `tracen` |
| Tracen Academy asset | `TracenAcademy_v4.0.zip`, `164227022` bytes, SHA-256 `0fa410c9bc983e39efb6cb905c7cefa65bf5000a4aa677b14ee7b5baa711be0d` |
| Mambo release | tag `v2.7.2`, release name `MatikaneTannhauser v2.8`, target `tracen` |
| Mambo asset | `Mambo_v2.8.zip`, `17862527` bytes, SHA-256 `7d2db5d7ada3698e60216be891c45ceab4d9532826cba2f37960f65a847021da` |
| License | GitHub API `license: null`; no `LICENSE` file is tracked at the inspected branch commit. License is unverified. |

The requested `/releases/tag/TracenAcademy_v4.0` URL is not the actual tag URL:
it redirects to the legacy-owner path and then returns `404`. The real release
tag is `v4.0`.

## Source Code And Tree Inspection

The shallow clone at commit `feed8f6d87d8745d58c84e2a83cfa244314bdf21` has 95
tracked paths. Its 23 C# files (2,938 lines) and project manifest were read.

- `Quirks/MediaManager.cs` resolves audio only as
  `Sounds/<startChar>/<fileName>` and plays it through local WPF
  `MediaPlayer` or `System.Media.SoundPlayer`.
- `Frames/SpriteManager.cs` resolves local sprite sheets under
  `SpriteSheet/Gremlins/<startChar>/...` and maps actions/emotes to PNG names.
- `Desktop_Gremlin.csproj` declares WAV files as `Content`; it has framework
  references only and no `PackageReference`.
- There are 27 tracked WAV files: 13 under `Sounds/Cafe`, 12 under
  `Sounds/Doto`, and 2 under `Sounds/Opera`. For example,
  `Sounds/Cafe/mambo.wav` is an actual RIFF/WAVE PCM mono file at 48 kHz,
  16-bit (SHA-256 `4985863D7486E3841C574EE89256E05E63D4BB26307AF1A96BB25AEBE1EEAA8E`).
- The name `mambo.wav` in `Cafe` or `Doto` is an action resource name, not
  evidence that either folder identifies the Mambo character.
- No source-code reference was found to `RVC`, `TTS`, Hugging Face,
  `WebClient`, `HttpClient`, `WebRequest`, `DownloadFile`, transcript, subtitle,
  or a model loader. `Process.Start(exePath)` is only the application's own
  restart action.
- No tracked path has `.pth`, `.index`, `.onnx`, `.gguf`, `.bin`, `.ckpt`,
  `.safetensors`, `.ogg`, `.mp3`, `.flac`, `.acb`, or `.awb`. Git attributes
  report no LFS filter for any tracked path.

The branch README mentions UmaViewer as the origin of sprite sheets and lists
release download links. That statement is retained only as upstream
documentation; it is not evidence for a Mambo voice model, dataset, or
transcript.

## ZIP Manifest Inspection

GitHub served both release assets with `Accept-Ranges: bytes`. Beta read only
the final 65,557 bytes of each ZIP (the complete central directory), then read
three small compressed text entries from `Mambo_v2.8.zip` by exact byte range.
No ZIP was downloaded or extracted.

| Archive | Complete central directory | Entries | Extensions in manifest | Mambo-specific evidence |
|---|---:|---:|---|---|
| `Mambo_v2.8.zip` | yes, 6,732-byte directory | 52 | 25 PNG, 8 WAV, 3 TXT, 1 ICO, 1 EXE, 14 directories | `Release/config.txt` sets `START_CHAR = Mambo`; `SpriteSheet/Gremlins/Mambo/config.txt`; eight WAV files in `Sounds/Mambo/` |
| `TracenAcademy_v4.0.zip` | yes, 44,577-byte directory | 361 | 193 PNG, 85 WAV, 11 TXT, 8 ICO, 2 EXE, 62 directories | `SpriteSheet/Gremlins/Mambo/` and eight WAV files in `Sounds/Mambo/` |

`Mambo_v2.8.zip` text entries read from the ZIP confirm local desktop-pet
configuration and sprite frame counts only. Its `readme.txt` references the
Desktop_Gremlin repository but no model repository, TTS, RVC, dataset, or
transcript source.

Neither complete ZIP manifest has a recognized voice-model artifact or a
transcript/subtitle artifact. The package EXE is present but was not downloaded,
opened, or run; therefore an embedded model is **unresolved**, not declared
absent.

## Evidence Table

| Source | Has | Model | Voice dataset | Transcript | Audio | License | URL | Evidence |
|---|---|---|---|---|---|---|---|---|
| Desktop_Gremlin `tracen` source | WPF desktop-pet source, sprites, local WAV playback | No recognized model file or loader/reference in inspected tree | None found | None found | 27 tracked WAV files | Unverified | `https://github.com/Kritzkingvoid/Desktop_Gremlin/tree/tracen` | Tree, C# source, `.csproj`, and Git attributes at `feed8f6d...` |
| `Mambo_v2.8.zip` release | Mambo desktop-pet package | No recognized model artifact in complete ZIP manifest; EXE internals unresolved | None found | None found | Eight `Sounds/Mambo/*.wav` entries | Unverified | `https://github.com/Kritzkingvoid/Desktop_Gremlin/releases/tag/v2.7.2` | GitHub release API, complete ZIP central directory, three exact text entries |
| `TracenAcademy_v4.0.zip` release | Multi-character desktop-pet package | No recognized model artifact in complete ZIP manifest; EXE internals unresolved | None found | No manifest evidence; 11 TXT entry contents not read | 85 WAV entries, eight in `Sounds/Mambo/` | Unverified | `https://github.com/Kritzkingvoid/Desktop_Gremlin/releases/tag/v4.0` | GitHub release API and complete ZIP central directory |
| UmaViewer | Sprite-sheet attribution in upstream README only | Not examined; no model URL/reference found in source or release text inspected | Not examined | Not examined | Not examined | Not verified here | No exact upstream URL was supplied by this trace | README-only attribution, not voice evidence |
| Hugging Face, RVC-Umamusume, umamusume voice/text extractors | No reference from inspected source, ZIP manifest, or Mambo release text | Not established | Not established | Not established | Not established | Not verified here | None discovered from this trace | No upstream reference to follow |

## Identity And Voice Conclusion

The release API name `MatikaneTannhauser v2.8`, package file name
`Mambo_v2.8.zip`, and `START_CHAR = Mambo` establish an upstream package mapping:
`mambo` -> release handle `MatikaneTannhauser` / package character ID `Mambo`.
They do not independently verify an official canonical character identity, so
the Beta profile remains `UNRESOLVED`.

The trace establishes that Mambo **audio resources** are in the two Desktop_Gremlin
release packages. It does **not** establish a Matikanetannhauser voice model,
base TTS model, RVC model, voice dataset, or transcript. No external model
repository URL is referenced by the inspected upstream source or release text.

## Import Boundary

- No local Tracen package was found in the limited local discovery roots.
- No upstream file is a Beta local voice reference or candidate sample.
- Do not copy, commit, upload, play, or use the upstream audio without a
  user-supplied local package, license review, and explicit approval.
