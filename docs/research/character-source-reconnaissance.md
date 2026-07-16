# Character Source Reconnaissance

This document summarizes the reconnaissance of external character sources required to verify the canonical identity of characters and acquire assets (avatars, audio, models) for local import.

**Important Rule:** Beta does NOT download or scrape these assets automatically. This research is used to inform the user of what they must provide locally.

---

## Source Reconnaissance Summary

| Source | Location / Repo | Purpose | Character Identity Mechanism | Avatar? | Audio? | Transcript? | Model? | Input Req | License/Status | Integration Difficulty |
|---|---|---|---|---|---|---|---|---|---|---|
| **Desktop_Gremlin / Tracen Academy** | `KurtVelasco/Desktop_Gremlin` (or Linux port `iluvgirlswithglasses/linux-desktop-gremlin`) | Identify canonical mascot & get desktop avatar | Config files or folder names within the package | ✅ Yes (Sprite/WPF/Qt6) | ❌ Usually No | ❌ No | ❌ No | Extracted package folder | Custom/Fan-made. May contain copyrighted sprites. | Low (Reading local config/images) |
| **UmaViewer** | `katboi01/UmaViewer` | Inspect 3D models, facial rigs, animations, metadata | In-game character IDs | ✅ Yes (3D) | ⚠️ Partial (Metadata) | ❌ No | ❌ No | Local game data path | Game assets belong to Cygames/DMM. | High (Needs Unity asset extraction) |
| **Voice Text Extractor** | `chinosk6/umamusume-voice-text-extractor` | Extract voice audio clips & transcripts | Game Character IDs | ❌ No | ✅ Yes (WAV/ACB) | ✅ Yes | ❌ No | Local game data path (DMM) | Extracted audio copyrighted by Cygames. | Medium (Tool automates extraction) |
| **RVC-Umamusume** | Hugging Face: `TLME/RVC-Umamusume` | RVC Voice Conversion models | Repo folder structure | ❌ No | ❌ No | ❌ No | ✅ Yes (RVC `.pth` + `.index`) | User downloads `.pth` & `.index` manually | Custom/Unknown. Trained on copyrighted data. | Medium (Needs RVC inference engine) |

---

## Detailed Source Breakdown

### 1. Desktop_Gremlin / Tracen Academy
- **Purpose:** A desktop pet/mascot application (often used for Umamusume, Blue Archive, Arknights characters).
- **Format:** C# WPF for Windows, or Python/Qt6 for Linux.
- **Character Identity:** Characters are usually identified by folder names or `config.txt` settings in the application directory.
- **Evidence:** Users report setting sprite scaling and selecting characters via config files. It uses 2D sprites or simple animations.
- **Current upstream check:** `KurtVelasco/Desktop_Gremlin` branch `tracen`
  exists at `feed8f6d87d8745d58c84e2a83cfa244314bdf21`. README/release metadata
  mention Tracen Academy packages, UmaViewer as the sheet source, and an outdated
  `Matikanetannhauser` package named `Mambo_v2.8.zip`. This is not sufficient to
  verify the local `mambo` profile without inspecting a user-supplied package.

### 2. UmaViewer
- **Purpose:** A tool to view 3D assets from the Uma Musume Pretty Derby game.
- **Format:** C# application. Reads Unity AssetBundles.
- **Character Identity:** Uses the canonical numeric IDs assigned by Cygames in the game's database.
- **Evidence:** Requires a local installation of the DMM version of the game to read the `master` database and asset bundles.

### 3. umamusume-voice-text-extractor
- **Purpose:** A Python/.NET tool to fetch, decrypt, and extract voice files (`.acb`, `.awb`) and story text from the game.
- **Format:** Outputs WAV/OGG files and JSON/TXT transcripts.
- **Character Identity:** Maps internal game IDs to character names. Extracts by character ID or scene.
- **Evidence:** Maintained by `chinosk6`. Requires Python 3.8+, .NET 6.0, and the DMM game client. Widely used for creating AI datasets.

### 4. RVC-Umamusume
- **Purpose:** Pre-trained Retrieval-based Voice Conversion (RVC) models.
- **Format:** RVC v2 `.pth` weights and `.index` feature files.
- **Character Identity:** Models are named after the characters (e.g., in the Hugging Face repo `TLME/RVC-Umamusume`).
- **Evidence:** Hosted on Hugging Face. Requires the RVC WebUI or a compatible inference script to run. Cannot be used for direct Text-to-Speech; requires a base TTS to generate source audio first.

---

## Conclusion
To fully realize a character like "mambo":
1. **Avatar:** Can be imported from Desktop_Gremlin sprites.
2. **Audio/Transcripts:** Can be extracted using the `umamusume-voice-text-extractor` from a local DMM game installation.
3. **Voice Conversion:** A pre-trained model can likely be downloaded from the `RVC-Umamusume` Hugging Face repository.

**Next Steps:** The user must provide the local paths to these extracted or downloaded assets before Beta can import them into `var/assets/`.
