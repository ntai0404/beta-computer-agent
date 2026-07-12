import pytest
from beta.infrastructure.character_assets.metadata.identity import (
    IdentityResolver,
    ResolutionStatus,
)


def test_identity_resolver_unresolved_alias_only():
    resolver = IdentityResolver("mambo")
    status, char_id = resolver.resolve()
    assert status == ResolutionStatus.UNRESOLVED
    assert char_id is None


def test_identity_resolver_candidate():
    resolver = IdentityResolver("mambo")
    resolver.add_evidence("desktop-gremlin", "matikanetannhauser", "medium", "folder")
    
    status, char_id = resolver.resolve()
    assert status == ResolutionStatus.CANDIDATE
    assert char_id == "matikanetannhauser"


def test_identity_resolver_verified_high():
    resolver = IdentityResolver("mambo")
    resolver.add_evidence("voice-dataset", "matikanetannhauser", "high", "metadata")
    
    status, char_id = resolver.resolve()
    assert status == ResolutionStatus.VERIFIED
    assert char_id == "matikanetannhauser"


def test_identity_resolver_verified_multiple_medium():
    resolver = IdentityResolver("mambo")
    resolver.add_evidence("desktop-gremlin", "matikanetannhauser", "medium", "folder")
    resolver.add_evidence("rvc-model", "matikanetannhauser", "medium", "filename")
    
    status, char_id = resolver.resolve()
    assert status == ResolutionStatus.VERIFIED
    assert char_id == "matikanetannhauser"


def test_identity_resolver_conflicting_high():
    resolver = IdentityResolver("mambo")
    resolver.add_evidence("voice-dataset", "matikanetannhauser", "high", "metadata")
    resolver.add_evidence("config", "other_char", "high", "config")
    
    status, char_id = resolver.resolve()
    assert status == ResolutionStatus.CONFLICTING
    assert char_id is None


def test_identity_resolver_conflicting_medium():
    resolver = IdentityResolver("mambo")
    resolver.add_evidence("desktop-gremlin", "matikanetannhauser", "medium", "folder")
    resolver.add_evidence("rvc-model", "other_char", "medium", "filename")
    
    status, char_id = resolver.resolve()
    assert status == ResolutionStatus.CONFLICTING
    assert char_id is None


def test_get_all_evidence():
    resolver = IdentityResolver("mambo")
    resolver.add_evidence("voice", "mati", "high", "ctx")
    
    ev = resolver.get_all_evidence()
    assert len(ev) == 2  # Includes the baseline user-alias evidence
    assert ev[0]["source"] == "user-alias"
    assert ev[1]["source"] == "voice"
    assert ev[1]["value"] == "mati"
