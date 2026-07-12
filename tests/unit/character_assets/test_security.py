import os
from pathlib import Path

import pytest
from beta.infrastructure.character_assets.validation.security import (
    PathTraversalError,
    ScanLimitExceededError,
    SecureScanner,
    SecurityScanError,
    categorize_file_by_extension,
    compute_sha256,
    is_path_safe,
)


def test_is_path_safe_allows_inside(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    target = root / "sub" / "file.txt"
    target.parent.mkdir()
    target.touch()
    
    assert is_path_safe(root, target) is True


def test_is_path_safe_rejects_outside(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.touch()
    
    assert is_path_safe(root, outside) is False


def test_compute_sha256(tmp_path: Path):
    file = tmp_path / "test.txt"
    file.write_text("hello world")
    
    # known sha256 for "hello world"
    expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert compute_sha256(file) == expected


def test_categorize_file_by_extension():
    assert categorize_file_by_extension(Path("test.png")) == "avatar_candidate"
    assert categorize_file_by_extension(Path("test.wav")) == "voice_candidate"
    assert categorize_file_by_extension(Path("test.txt")) == "metadata_candidate"
    assert categorize_file_by_extension(Path("test.pth")) == "rvc_candidate"
    assert categorize_file_by_extension(Path("test.exe")) == "executable_blocked"
    assert categorize_file_by_extension(Path("test.dll")) == "executable_blocked"
    assert categorize_file_by_extension(Path("test.unknown")) == "unknown"


def test_secure_scanner_basic(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "1.txt").touch()
    (root / "2.png").touch()
    
    scanner = SecureScanner(root)
    files = list(scanner.scan())
    
    assert len(files) == 2
    assert sorted([f.name for f in files]) == ["1.txt", "2.png"]


def test_secure_scanner_ignores_symlink_escape(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "safe.txt").touch()
    
    outside = tmp_path / "outside.txt"
    outside.touch()
    
    # Create symlink pointing outside
    try:
        os.symlink(outside, root / "escape_link")
    except OSError:
        pytest.skip("Symlinks not supported on this OS/user")
        
    scanner = SecureScanner(root)
    files = list(scanner.scan())
    
    assert len(files) == 1
    assert files[0].name == "safe.txt"


def test_secure_scanner_follows_internal_symlink(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "safe.txt").touch()
    
    # Create symlink pointing inside
    try:
        os.symlink(root / "safe.txt", root / "internal_link")
    except OSError:
        pytest.skip("Symlinks not supported on this OS/user")
        
    scanner = SecureScanner(root)
    files = list(scanner.scan())
    
    assert len(files) == 2
    assert sorted([f.name for f in files]) == ["internal_link", "safe.txt"]
