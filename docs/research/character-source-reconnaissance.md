# Character Source Reconnaissance

## Current Evidence: Mambo

This record separates evidence obtained from Desktop_Gremlin from possible
third-party sources that have not been evidenced for the `mambo` profile.
Beta does not download, import, or use assets as part of this reconnaissance.

| Source | Status for `mambo` | Model | Dataset | Transcript | Audio | Evidence |
|---|---|---|---|---|---|---|
| Desktop_Gremlin `tracen` source | Inspected at `feed8f6d87d8745d58c84e2a83cfa244314bdf21` | No recognized model artifact or code reference | None found | None found | 27 tracked WAV files, but none is a Beta local reference | Source tree, 23 C# files, project manifest |
| Desktop_Gremlin `Mambo_v2.8.zip` | Release package mapping verified | No recognized model artifact in complete ZIP directory; EXE internals unresolved | None found | None found | Eight `Sounds/Mambo/*.wav` entries | Release API, complete ZIP directory, config `START_CHAR = Mambo` |
| Desktop_Gremlin `TracenAcademy_v4.0.zip` | Multi-character package includes Mambo mapping | No recognized model artifact in complete ZIP directory; EXE internals unresolved | None found | No manifest evidence | 85 WAV entries; eight under `Sounds/Mambo/` | Release API and complete ZIP directory |
| UmaViewer | Upstream README-only sprite attribution | Not examined | Not examined | Not examined | Not examined | Not voice evidence; no exact URL found by this trace |
| umamusume voice/text extractor | Not referenced by inspected upstream | Not established | Not established | Not established | Not established | No upstream URL/reference to follow |
| Hugging Face / RVC-Umamusume | Not referenced by inspected upstream | Not established | Not established | Not established | Not established | No upstream URL/reference to follow |

## Identity Status

The Mambo release display name is `MatikaneTannhauser v2.8`; its release package
is `Mambo_v2.8.zip`; and its internal desktop-pet config says `START_CHAR = Mambo`.
This is source/package mapping evidence. It does not independently establish the
official canonical identity of the Beta `mambo` profile, which remains
`UNRESOLVED`.

## Voice Status

Desktop_Gremlin is an audio-resource source, not an evidenced voice-model source.
No TTS model, RVC model, voice dataset, transcript, or external model repository
was found in its inspected branch source, release manifests, or Mambo release
text files. A package EXE was deliberately not downloaded, opened, or run, so
its embedded contents are unresolved.

The source package audio is neither a synthetic fixture nor a verified local
Beta reference. It must not be copied, uploaded, or treated as character-matched
speech without user-supplied local evidence, license review, and approval.
