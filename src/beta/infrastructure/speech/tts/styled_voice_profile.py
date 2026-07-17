"""Small cached profile format for prebuilt styled TTS voices."""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from pathlib import Path

from beta.infrastructure.character_assets.validation.security import compute_sha256


@dataclass(frozen=True)
class StyledVoiceProfile:
    base_voice: str
    style_prompt: str
    analyzer_model: str
    source_sample_hashes: tuple[str, ...]
    generated_at: str
    label: str
    clone_status: str


def build_styled_voice_profile(
    profile_path: Path,
    *,
    sample_paths: list[Path],
    base_voice: str,
    style_prompt: str,
    analyzer_model: str,
    label: str,
    clone_status: str,
) -> tuple[StyledVoiceProfile, bool]:
    """Cache local sample provenance; this function does not call a cloud analyzer."""
    hashes = tuple(compute_sha256(path) for path in sample_paths if path.is_file())
    if not hashes:
        raise FileNotFoundError("No local WAV samples were available for profile provenance.")

    if profile_path.exists():
        existing = load_styled_voice_profile(profile_path)
        if existing.source_sample_hashes == hashes:
            return existing, False

    profile = StyledVoiceProfile(
        base_voice=base_voice,
        style_prompt=style_prompt,
        analyzer_model=analyzer_model,
        source_sample_hashes=hashes,
        generated_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        label=label,
        clone_status=clone_status,
    )
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(_serialize(profile), encoding="utf-8")
    return profile, True


def load_styled_voice_profile(profile_path: Path) -> StyledVoiceProfile:
    """Read the deliberately small YAML subset used by Beta voice profiles."""
    try:
        lines = profile_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise FileNotFoundError(f"Voice profile not found: {profile_path}") from exc

    values: dict[str, str] = {}
    hashes: list[str] = []
    reading_hashes = False
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "source_sample_hashes:":
            reading_hashes = True
            continue
        if reading_hashes and line.startswith("- "):
            hashes.append(_unquote(line[2:].strip()))
            continue
        reading_hashes = False
        key, separator, value = line.partition(":")
        if separator:
            values[key.strip()] = _unquote(value.strip())

    required = (
        "base_voice",
        "style_prompt",
        "analyzer_model",
        "generated_at",
        "label",
        "clone_status",
    )
    missing = [key for key in required if not values.get(key)]
    if missing or not hashes:
        raise ValueError(f"Invalid styled voice profile: missing {', '.join(missing or ['source_sample_hashes'])}")
    return StyledVoiceProfile(
        base_voice=values["base_voice"],
        style_prompt=values["style_prompt"],
        analyzer_model=values["analyzer_model"],
        source_sample_hashes=tuple(hashes),
        generated_at=values["generated_at"],
        label=values["label"],
        clone_status=values["clone_status"],
    )


def _serialize(profile: StyledVoiceProfile) -> str:
    lines = [
        f"base_voice: {_quote(profile.base_voice)}",
        f"style_prompt: {_quote(profile.style_prompt)}",
        f"analyzer_model: {_quote(profile.analyzer_model)}",
        "source_sample_hashes:",
    ]
    lines.extend(f"  - {_quote(sample_hash)}" for sample_hash in profile.source_sample_hashes)
    lines.extend(
        (
            f"generated_at: {_quote(profile.generated_at)}",
            f"label: {_quote(profile.label)}",
            f"clone_status: {_quote(profile.clone_status)}",
            "",
        )
    )
    return "\n".join(lines)


def _quote(value: str) -> str:
    return '"' + value.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    return value
