# Character Asset Import Plan

This document outlines the architecture and workflow for importing external, user-supplied character assets into Beta's local storage (`var/assets/`).

**Goal:** Safely validate, hash, and store user-provided files without downloading from the internet or making assumptions about canonical identity.

---

## Import Flow

```text
External local source (User provides path: C:\Downloads\Model.pth)
 │
 ▼
1. Source Detector
   (Determines if path is an RVC model, an audio folder, a Gremlin package, etc.)
 │
 ▼
2. Metadata Reader
   (Extracts metadata: file size, format, sample rate, internal names)
 │
 ▼
3. Character Identity Resolver
   (Attempts to read canonical character ID from the source metadata, if present)
 │
 ▼
4. Asset Validator
   (Checks if the file is valid/corrupt, e.g., is it a real WAV? A real .pth?)
 │
 ▼
5. Import Manifest Generation
   (Creates a JSON manifest recording the provenance of the asset)
 │
 ▼
6. Asset Copy/Link
   (Places the file into var/assets/characters/<profile_id>/...)
```

---

## The Import Manifest

Every imported asset will have an accompanying metadata entry in `import-plan.json` initially, and eventually stored in `var/assets/characters/<profile_id>/metadata/`.

**Concept Schema (`import-plan.json`):**
```json
[
  {
    "source_type": "desktop-gremlin",
    "source_path": "C:\\Users\\example\\Desktop_Gremlin\\Models\\matikanetannhauser\\sprite.png",
    "imported_at": null,
    "canonical_character_id": "matikanetannhauser",
    "persona_alias": "mambo",
    "asset_type": "avatar_candidate",
    "original_filename": "sprite.png",
    "destination_path": "var/assets/characters/mambo/avatar/sprite.png",
    "checksum": "sha256_hash_here",
    "license_note": "User-supplied external asset.",
    "provenance": "Local file inspection.",
    "validation_status": "pending_approval"
  }
]
```

---

## Principles for Importer Scripts

1. **Read-Only on Source:** The import script MUST NOT modify the files in the user-supplied source directory.
2. **No Cloud Calls:** The import script MUST NOT upload the asset or phone home.
3. **No DRM Bypass:** If an asset is encrypted (e.g., `.acb` files without a key), the script fails gracefully. It does not attempt to break encryption.
4. **Strict Hashing:** Every asset gets a SHA-256 hash immediately upon read.

*(Note: Full importer implementation is deferred to a future milestone. Currently, we only define the boundary and plan.)*
