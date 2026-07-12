# Mambo Identity Resolution

This document tracks the investigation into the canonical identity of the persona alias `"mambo"`.

**Alias:** `mambo`
**Current Status:** UNRESOLVED

---

## Candidate Canonical Identities

Based on community research and game lore, there are two primary candidates for the alias "mambo" within the *Uma Musume: Pretty Derby* context.

### Candidate 1: Matikanetannhauser (Machikanetannhauser)
- **Description:** An Umamusume character.
- **Evidence For:**
  - **The "Omatsuri Mambo" Chant:** In her character story, she sings a specific line: *"Mambo~ Mambou~! Wasshoi Mambo~u♪"*.
  - **Meme Culture:** Due to her long name and this specific chant, the Chinese-speaking community (and subsequently the global community via Bilibili, TikTok, YouTube) started calling her "Mambo". Her voice is frequently used in AI meme songs under this nickname.
- **Evidence Against:**
  - "Mambo" is purely a fan-made nickname. Her canonical game name is Matikanetannhauser (Machikanetannhauser).

### Candidate 2: Mambo (El Condor Pasa's pet hawk)
- **Description:** A pet hawk belonging to the character El Condor Pasa.
- **Evidence For:**
  - The hawk's canonical, official name in the game is literally "Mambo".
- **Evidence Against:**
  - The hawk is an animal, not a speaking Umamusume character. It does not have voice lines or a desktop avatar in the same way the girls do. When fans use the term "Mambo" in the context of AI voices or desktop pets, they are almost exclusively referring to the meme surrounding Matikanetannhauser.

---

## Confidence and Conclusion

**Confidence:** High (regarding community usage).

**Conclusion:**
When the user refers to "Mambo" as a voice/desktop assistant persona, it is highly probable they mean **Matikanetannhauser**.

However, Beta operates strictly on verifiable canonical metadata. We cannot hardcode this assumption.

**Unresolved Questions:**
1. Does the user's specific `Desktop_Gremlin` package label the folder/config as `mambo` or `matikanetannhauser`?
2. Does the user intend to use the voice of Matikanetannhauser?

**Action Required:**
Do NOT change the `canonical_character_id` in the profile yet.
Wait for the user to import the `Desktop_Gremlin` package or `RVC` model. The import boundary script will read the local folder names or metadata provided by the user to finalize the canonical identity.
