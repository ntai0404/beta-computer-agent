from pathlib import Path

from beta.infrastructure.speech.tts.styled_voice_profile import (
    build_styled_voice_profile,
    load_styled_voice_profile,
)


def test_profile_build_caches_unchanged_sample_hashes(tmp_path: Path):
    samples = [tmp_path / "first.wav", tmp_path / "second.wav"]
    samples[0].write_bytes(b"RIFF-first")
    samples[1].write_bytes(b"RIFF-second")
    profile_path = tmp_path / "voice.yaml"

    profile, changed = build_styled_voice_profile(
        profile_path,
        sample_paths=samples,
        base_voice="Kore",
        style_prompt="Bright and lively.",
        analyzer_model="local-provenance-hash-only",
        label="mambo-inspired-gemini-tts",
        clone_status="not_cloned",
    )
    cached, changed_again = build_styled_voice_profile(
        profile_path,
        sample_paths=samples,
        base_voice="DifferentBaseVoiceIgnoredWhenCached",
        style_prompt="Ignored when cached.",
        analyzer_model="local-provenance-hash-only",
        label="mambo-inspired-gemini-tts",
        clone_status="not_cloned",
    )

    assert changed is True
    assert changed_again is False
    assert cached == profile
    assert load_styled_voice_profile(profile_path) == profile
