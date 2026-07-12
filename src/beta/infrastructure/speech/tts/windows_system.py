"""
infrastructure/speech/tts/windows_system.py

TTS provider that uses Windows System.Speech.Synthesis via PowerShell.

Security contract:
  - User text is NEVER interpolated into the PowerShell command string.
  - Text is written to a UTF-8 temp file and read by the script at runtime.
  - subprocess is called WITHOUT shell=True.
  - Temp files are always cleaned up.

No MAS runtime, agent, or business logic belongs here.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from beta.interaction.voice.contracts import (
    SpeechArtifact,
    SpeechRequest,
)
from beta.interaction.voice.errors import AudioOutputError, TtsProviderError
from beta.infrastructure.speech.tts.base import TtsProvider, VoiceInfo

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT_SECONDS: int = 60
# windows_system.py lives at: src/beta/infrastructure/speech/tts/windows_system.py
# parents: [0]=tts, [1]=speech, [2]=infrastructure, [3]=beta, [4]=src, [5]=project_root
_PROJECT_ROOT = Path(__file__).resolve().parents[5]
_DEFAULT_OUTPUT_DIR = _PROJECT_ROOT / "var" / "artifacts" / "audio"

# ---------------------------------------------------------------------------
# PowerShell script templates (no user input interpolated here)
# ---------------------------------------------------------------------------

# Script that reads text from a file, synthesizes, and writes WAV.
# Arguments are passed via JSON sidecar to avoid any injection surface.
_SYNTH_SCRIPT = r"""
param([string]$ConfigPath)

$ErrorActionPreference = 'Stop'

$cfg = Get-Content -Path $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json

Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer

try {
    if ($cfg.voice_name -and $cfg.voice_name -ne '') {
        try {
            $synth.SelectVoice($cfg.voice_name)
        } catch {
            # Voice not found — use system default and add a warning
            $null | Out-File -FilePath ($cfg.output_path + '.warn') -Encoding UTF8
        }
    }

    $synth.Rate   = [int]$cfg.rate
    $synth.Volume = [int]$cfg.volume

    $parent = Split-Path -Parent $cfg.output_path
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }

    $synth.SetOutputToWaveFile($cfg.output_path)
    $synth.Speak($cfg.text)
    $synth.SetOutputToDefaultAudioDevice()

    # Emit selected voice name as JSON for the caller to capture
    $selectedVoice = $synth.Voice.Name
    @{ voice = $selectedVoice } | ConvertTo-Json -Compress
} finally {
    $synth.Dispose()
}
"""

# Script that lists installed voices and returns JSON.
_LIST_VOICES_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $voices = $synth.GetInstalledVoices() | ForEach-Object {
        $info = $_.VoiceInfo
        @{
            name     = $info.Name
            language = $info.Culture.Name
            gender   = $info.Gender.ToString()
            desc     = $info.Description
        }
    }
    $voices | ConvertTo-Json -Depth 3
} finally {
    $synth.Dispose()
}
"""


class WindowsSystemTtsProvider(TtsProvider):
    """
    TTS provider backed by Windows System.Speech.Synthesis (SAPI).

    Requires Windows with at least one SAPI voice installed.
    No network calls. No models. No API keys.
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        timeout: int = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._output_dir = (output_dir or _DEFAULT_OUTPUT_DIR).resolve()
        self._timeout = timeout

    @property
    def provider_id(self) -> str:
        return "windows-system"

    # ------------------------------------------------------------------
    # synthesize
    # ------------------------------------------------------------------

    def synthesize(self, request: SpeechRequest) -> SpeechArtifact:
        """
        Synthesize speech and write a WAV file.

        Security: text is passed via a JSON temp file, never via CLI args.
        """
        output_path = self._resolve_output_path(request.output_path)
        _ensure_dir(output_path.parent)
        _guard_no_overwrite(output_path)

        config_file: Optional[Path] = None
        script_file: Optional[Path] = None
        warn_marker = Path(str(output_path) + ".warn")

        try:
            # --- Build JSON config (text lives here, not on the command line)
            config = {
                "text": request.text,
                "voice_name": "",
                "rate": request.rate,
                "volume": request.volume,
                "output_path": str(output_path),
            }

            # --- Write config to temp file
            config_file = _write_temp_json(config)
            script_file = _write_temp_ps1(_SYNTH_SCRIPT)

            result = _run_powershell(
                script_file, config_file, self._timeout
            )

            # Parse selected voice name from stdout
            voice_name: Optional[str] = None
            try:
                data = json.loads(result.stdout.strip())
                voice_name = data.get("voice")
            except Exception:
                pass  # non-fatal

            warnings: list[str] = []
            if warn_marker.exists():
                warnings.append(
                    f"Requested voice not found; system default was used."
                )
                warn_marker.unlink(missing_ok=True)

            if not output_path.exists():
                raise AudioOutputError(
                    f"Provider reported success but WAV not found: {output_path}"
                )

            size = output_path.stat().st_size
            if size == 0:
                raise AudioOutputError(
                    f"Provider wrote an empty WAV file: {output_path}"
                )

            artifact = SpeechArtifact(
                path=output_path,
                format="wav",
                provider=self.provider_id,
                voice_name=voice_name,
                size_bytes=size,
                created_at=datetime.now(timezone.utc),
                metadata={"warnings": warnings},
            )
            logger.info(
                "Synthesized %d bytes → %s (voice=%s)",
                size,
                output_path,
                voice_name,
            )
            return artifact

        except (TtsProviderError, AudioOutputError):
            raise
        except Exception as exc:
            raise TtsProviderError(
                f"WindowsSystemTtsProvider synthesis failed: {exc}"
            ) from exc
        finally:
            _cleanup(config_file)
            _cleanup(script_file)

    # ------------------------------------------------------------------
    # list_voices
    # ------------------------------------------------------------------

    def list_voices(self) -> list[VoiceInfo]:
        """Return all SAPI voices installed on this Windows machine."""
        script_file: Optional[Path] = None
        try:
            script_file = _write_temp_ps1(_LIST_VOICES_SCRIPT)
            result = _run_powershell_script_only(script_file, self._timeout)
            raw = result.stdout.strip()
            if not raw:
                return []
            data = json.loads(raw)
            if isinstance(data, dict):
                data = [data]
            return [
                VoiceInfo(
                    name=v.get("name", ""),
                    language=v.get("language", ""),
                    gender=v.get("gender"),
                    description=v.get("desc"),
                )
                for v in data
                if v.get("name")
            ]
        except Exception as exc:
            logger.warning("list_voices failed: %s", exc)
            return []
        finally:
            _cleanup(script_file)

    # ------------------------------------------------------------------
    # health_check
    # ------------------------------------------------------------------

    def health_check(self) -> None:
        """Raise TtsProviderError if System.Speech is unavailable."""
        voices = self.list_voices()
        if not voices:
            raise TtsProviderError(
                "No SAPI voices found on this Windows system. "
                "Install a TTS voice via Settings → Time & Language → Speech."
            )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_output_path(self, requested: Optional[Path]) -> Path:
        if requested is not None:
            return requested.resolve()
        unique = f"speech_{uuid.uuid4().hex[:12]}.wav"
        return self._output_dir / unique


# ---------------------------------------------------------------------------
# Module-level helpers (private)
# ---------------------------------------------------------------------------


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _guard_no_overwrite(path: Path) -> None:
    if path.exists():
        raise AudioOutputError(
            f"Output file already exists and overwrite is not permitted: {path}"
        )


def _write_temp_json(data: dict) -> Path:
    fd, name = tempfile.mkstemp(suffix=".json", prefix="beta_tts_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
    except Exception:
        os.unlink(name)
        raise
    return Path(name)


def _write_temp_ps1(script: str) -> Path:
    fd, name = tempfile.mkstemp(suffix=".ps1", prefix="beta_tts_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(script)
    except Exception:
        os.unlink(name)
        raise
    return Path(name)


def _run_powershell(
    script: Path, config: Path, timeout: int
) -> subprocess.CompletedProcess:
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", str(script),
        str(config),
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            shell=False,  # explicit: never use shell=True
        )
    except subprocess.TimeoutExpired as exc:
        raise TtsProviderError(
            f"TTS synthesis timed out after {timeout}s."
        ) from exc
    except FileNotFoundError as exc:
        raise TtsProviderError(
            "powershell.exe not found. Windows TTS requires PowerShell."
        ) from exc

    if result.returncode != 0:
        raise TtsProviderError(
            f"PowerShell exited {result.returncode}.\n"
            f"stderr: {result.stderr.strip()}"
        )
    return result


def _run_powershell_script_only(
    script: Path, timeout: int
) -> subprocess.CompletedProcess:
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy", "Bypass",
        "-File", str(script),
    ]
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=timeout,
            shell=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise TtsProviderError(f"list_voices timed out after {timeout}s.") from exc


def _cleanup(path: Optional[Path]) -> None:
    if path and path.exists():
        try:
            path.unlink()
        except OSError as exc:
            logger.warning("Failed to clean up temp file %s: %s", path, exc)
