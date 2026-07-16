# External Source: Desktop_Gremlin / Tracen Academy

**Source name:** Desktop_Gremlin (Tracen Academy package)  
**Purpose:** Identify canonical mascot character packaged in the application  
**Import status:** NOT STARTED  

---

## Purpose

Examine this package to determine:

- The real canonical name of the mascot/character included.
- The canonical character ID used in asset files.
- The format and content of sprite and animation assets.
- Whether the package contains audio.
- What license governs the use of bundled assets.

Beta does NOT assume this package contains "Mambo" or any specific character.
The canonical identity must be read from the package metadata directly.

---

## Expected Asset Types

| Asset Type | Expected Format | Notes |
|---|---|---|
| Character sprite | PNG, sprite sheet, atlas | May be in a proprietary format |
| Desktop model | Live2D, spine2d, or similar | Format unknown until inspected |
| Animations | Bundled with model | May require runtime library |
| Audio clips | WAV, OGG, or similar | Presence unknown |
| Character metadata | JSON, XML, or embedded | Canonical name/ID lives here |

---

## Upstream Location

| Field | Value |
|---|---|
| Repository / product | Desktop_Gremlin / Tracen Academy |
| Canonical repository URL checked | `https://github.com/KurtVelasco/Desktop_Gremlin` |
| Redirect/legacy owner observed | GitHub API responses may reference `Kritzkingvoid/Desktop_Gremlin` |
| Branch checked | `tracen` |
| Branch ref checked | `feed8f6d87d8745d58c84e2a83cfa244314bdf21` |
| Branch check command | `git ls-remote https://github.com/KurtVelasco/Desktop_Gremlin.git refs/heads/tracen` |
| Release requested by user | `https://github.com/KurtVelasco/Desktop_Gremlin/releases/tag/TracenAcademy_v4.0` |
| Requested release URL result | HTTP 301 to legacy owner, then 404 |
| Release metadata checked | GitHub release tag `v4.0`, release name `TracenAcademy_v4.0` |
| Release asset metadata | `TracenAcademy_v4.0.zip`, size `164227022`, digest `sha256:0fa410c9bc983e39efb6cb905c7cefa65bf5000a4aa677b14ee7b5baa711be0d` |
| Download method | User-supplied local extracted package only |
| Version / tag | `v4.0`; no release asset downloaded by Beta |

## Upstream Reconnaissance

Read-only upstream checks found:

- README lists Tracen Academy releases and says the sheets come from UmaViewer.
- README lists an outdated `Matikanetannhauser` entry with package name
  `Mambo_v2.8.zip`.
- Shallow clone of branch `tracen` found source folders `SpriteSheet/Gremlins/Cafe`,
  `Sounds/Cafe`, `Sounds/Doto`, and `Sounds/Opera`.
- Source sound mapping exists: `MediaManager.PlaySound(fileName, startChar)` resolves
  `Sounds/<startChar>/<fileName>`, and code calls examples such as `intro.wav`,
  `sleep.wav`, `outro.wav`, and `grab.wav`.
- Source emote/action mapping exists: `SpriteManager` maps `emote1`-`emote4`,
  `intro`, `idle`, `hover`, `grab`, `sleep`, `outro`, walk/run directions, and
  related actions to PNG sprite names.
- GitHub releases on branch `tracen` include package metadata such as release
  names, asset names, sizes, and SHA-256 digests.
- No release asset was downloaded by Beta during reconnaissance.

This is provenance evidence only. It is not enough to mark the local `mambo`
profile as verified. Verification still requires a user-supplied local package
and metadata inspection. Source WAV files in an upstream clone are not counted
as verified local voice references for Beta.

---

## Import Status

| Step | Status |
|---|---|
| User supplies local path | ⬜ Not done |
| Package structure inspected | ⬜ Not done |
| Canonical character name identified | ⬜ Not done |
| Canonical character ID identified | ⬜ Not done |
| Asset format documented | ⬜ Not done |
| License verified | ⬜ Not done |
| Assets placed in var/assets/ | ⬜ Not done |
| Character profile updated | ⬜ Not done |

---

## License Status

**Not verified.**

Before importing any assets from this package, the applicable license must be reviewed.
Assets may NOT be redistributed or committed to Git without explicit permission.

---

## User-Supplied Path

*(Not provided. User must supply the local path to the installed or extracted package.)*

---

## Warnings

- Do NOT commit package assets to Git.
- Do NOT assume asset ownership without reading the license.
- Do NOT assume the character in this package is "Mambo" without verification.
- Beta's import boundary validates assets before placing them in var/assets/.

---

## Last Verified

Never.
