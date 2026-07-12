"""
infrastructure/character_assets/validation/security.py

Security module for scanning and validating local assets.
Ensures no path traversal, no symlink escapes, and enforces limits.
Computes checksums.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

MAX_FILES_PER_SCAN = 10_000
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB

# Known file extensions. We do NOT load or execute any of these.
_SUPPORTED_AVATAR_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
_SUPPORTED_VOICE_EXTS = {".wav", ".ogg", ".flac", ".mp3", ".acb", ".awb"}
_SUPPORTED_TRANSCRIPT_EXTS = {".csv", ".tsv"}
_SUPPORTED_METADATA_EXTS = {".json", ".txt"}
_SUPPORTED_RVC_EXTS = {".pth", ".index"}


class SecurityScanError(Exception):
    """Base exception for security scanning errors."""


class PathTraversalError(SecurityScanError):
    """Raised when a path attempts to escape the root directory."""


class SymlinkEscapeError(SecurityScanError):
    """Raised when a symlink points outside the root directory."""


class ScanLimitExceededError(SecurityScanError):
    """Raised when a directory contains too many files or a file is too large."""


def is_path_safe(root_dir: Path, target_path: Path) -> bool:
    """
    Check if target_path resolves strictly within root_dir.
    Raises an error if it escapes.
    """
    try:
        resolved_root = root_dir.resolve(strict=True)
        # We don't use strict=True for target because it might be a symlink we want to reject gracefully,
        # or it might not exist yet if we're just validating a theoretical path.
        resolved_target = target_path.resolve()
        
        # Check if resolved_target is relative to resolved_root
        # This will raise ValueError if it's on a different drive on Windows
        resolved_target.relative_to(resolved_root)
        return True
    except ValueError:
        return False
    except FileNotFoundError:
        # If root doesn't exist, it's not safe to operate
        raise SecurityScanError(f"Root directory does not exist: {root_dir}")


def compute_sha256(path: Path) -> str:
    """Safely compute SHA-256 checksum of a file without loading it all into memory."""
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    
    if path.stat().st_size > MAX_FILE_SIZE_BYTES:
        raise ScanLimitExceededError(f"File too large to hash: {path.name}")

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


class SecureScanner:
    """
    Safely walks a directory yielding Path objects.
    Enforces security bounds: path traversal, symlinks, file limits.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir.resolve(strict=True)

    def scan(self) -> Iterator[Path]:
        """
        Yields all safe files within the root directory recursively.
        """
        file_count = 0
        
        # We use a stack to manually walk so we can strictly control symlink resolution
        stack = [self.root_dir]
        
        while stack:
            current_dir = stack.pop()
            
            try:
                for entry in current_dir.iterdir():
                    if entry.is_symlink():
                        # Resolve symlink and check if it escapes
                        resolved_symlink = entry.resolve()
                        try:
                            resolved_symlink.relative_to(self.root_dir)
                        except ValueError:
                            logger.warning(f"Skipping symlink escape: {entry}")
                            continue
                            
                    if entry.is_file():
                        file_count += 1
                        if file_count > MAX_FILES_PER_SCAN:
                            raise ScanLimitExceededError(
                                f"Exceeded maximum files per scan ({MAX_FILES_PER_SCAN})"
                            )
                        
                        if entry.stat().st_size > MAX_FILE_SIZE_BYTES:
                            logger.warning(f"Skipping file exceeding size limit: {entry}")
                            continue
                            
                        yield entry
                        
                    elif entry.is_dir():
                        stack.append(entry)
                        
            except PermissionError:
                logger.warning(f"Permission denied scanning directory: {current_dir}")
                continue


def categorize_file_by_extension(path: Path) -> str:
    """
    Returns a string category based purely on extension.
    Does NOT inspect file contents.
    """
    ext = path.suffix.lower()
    if ext in _SUPPORTED_AVATAR_EXTS:
        return "avatar_candidate"
    if ext in _SUPPORTED_VOICE_EXTS:
        return "voice_candidate"
    if ext in _SUPPORTED_TRANSCRIPT_EXTS:
        return "transcript_candidate"
    if ext in _SUPPORTED_METADATA_EXTS:
        return "metadata_candidate"
    if ext in _SUPPORTED_RVC_EXTS:
        return "rvc_candidate"
    
    # Executables are explicitly categorized as dangerous/unsupported
    if ext in {".exe", ".dll", ".bat", ".cmd", ".ps1", ".sh", ".vbs"}:
        return "executable_blocked"
        
    return "unknown"
