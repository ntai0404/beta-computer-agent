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

## 2. The Import Plan (`import-plan.json`)

**Concept Schema:**
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

## 3. The Provenance Manifest (`import-manifest_*.json`)

After executing an import batch, a provenance manifest is saved to `var/assets/characters/<profile_id>/metadata/`. This serves as an audit trail for the assets actually copied into the internal storage.

**Concept Schema:**
```json
[
  {
    "source_type": "desktop-gremlin",
    "source_path": "C:\\Users\\example\\Desktop_Gremlin\\Models\\matikanetannhauser\\sprite.png",
    "imported_at": "2026-07-12T10:30:00Z",
    "canonical_character_id": "matikanetannhauser",
    "persona_alias": "mambo",
    "asset_type": "avatar_candidate",
    "original_filename": "sprite.png",
    "destination_path": "var/assets/characters/mambo/avatar/sprite.png",
    "checksum": "sha256_hash_here",
    "import_status": "imported",
    "license_note": "User-supplied external asset.",
    "provenance": "Local file inspection."
  }
]
```

Valid `import_status` values:
- `imported`: Asset successfully copied.
- `already_present`: Asset existed with identical checksum; skipped copy.
- `skipped`: Asset was not in the approval list.
- `conflict`: Destination existed with a different checksum; aborted copy.
- `failed`: An error occurred during validation or atomic copy.

---

## Principles for Importer Scripts

1. **Read-Only on Source:** The import script MUST NOT modify the files in the user-supplied source directory.
2. **No Cloud Calls:** The import script MUST NOT upload the asset or phone home.
3. **No DRM Bypass:** If an asset is encrypted (e.g., `.acb` files without a key), the script fails gracefully. It does not attempt to break encryption.
4. **Strict Hashing:** Every asset gets a SHA-256 hash immediately upon read.

*(Note: Full importer implementation is deferred to a future milestone. Currently, we only define the boundary and plan.)*
