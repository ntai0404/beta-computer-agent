# External Source: UmaViewer / Uma Musume Asset Reader

**Source name:** UmaViewer (or equivalent tool)  
**Purpose:** Read Uma Musume character models, animations, and metadata  
**Import status:** NOT STARTED  

---

## Purpose

Use this tool to examine:

- Character 3D model and its ID in the game database.
- Available animations (idle, talk, expression).
- Facial animation rig (blendshapes, bones).
- Any voice metadata attached to the character.
- Canonical character ID as used in game data.

Beta does NOT assume a specific character ID without reading game data.

---

## Expected Asset Types

| Asset Type | Expected Format | Notes |
|---|---|---|
| 3D character model | Unity asset bundle, converted FBX/GLB | Requires extraction tool |
| Animations | Unity animation clips | Requires runtime or export |
| Facial rig | Blendshapes / morph targets | Format depends on extraction |
| Character metadata | JSON from game database | Canonical ID found here |
| Voice metadata | Scene/event data | If present |

---

## Upstream Location

| Field | Value |
|---|---|
| Tool name | UmaViewer |
| Repository | `https://github.com/UmaViewerDev/UmaViewer` (or equivalent) |
| Asset origin | Uma Musume Pretty Derby (Cygames / DMM) |
| User-supplied asset path | *(not provided)* |

---

## Import Status

| Step | Status |
|---|---|
| Tool installed | ⬜ Not done |
| Game asset path supplied | ⬜ Not done |
| Target character identified | ⬜ Not done |
| Canonical character ID read | ⬜ Not done |
| Model format documented | ⬜ Not done |
| License reviewed | ⬜ Not done |
| Model placed in var/assets/ | ⬜ Not done |

---

## License Status

**Not verified.**

Game assets belong to Cygames / DMM. Extracted assets may be subject to:
- Terms of Service of Uma Musume Pretty Derby.
- Copyright law in the user's jurisdiction.

Do NOT redistribute extracted assets. Do NOT commit to Git.

---

## Warnings

- UmaViewer reads assets; it does not grant rights to use them.
- Canonical character ID must be verified from game metadata before updating character profile.
- Do NOT assume the character visible in UmaViewer matches the "mambo" alias without explicit verification.

---

## Last Verified

Never.
