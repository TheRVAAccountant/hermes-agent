from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from hermes_constants import get_hermes_home
from hermes_cli.providers import custom_provider_slug

_SAFE_ACTION = re.compile(r"^[a-zA-Z0-9_-]+$")
_active_server_action = ""


@dataclass(frozen=True)
class LocalServerResult:
    ran: bool
    action: str = ""
    stdout: str = ""
    stderr: str = ""


def active_server_action() -> str:
    return _active_server_action


def mark_active_server_action(action: str) -> None:
    global _active_server_action
    _active_server_action = action.strip() if isinstance(action, str) else ""


def _safe_action(action: str) -> str:
    cleaned = (action or "").strip()
    if not cleaned:
        return ""
    if not _SAFE_ACTION.fullmatch(cleaned):
        return ""
    return cleaned


def _provider_matches_entry(provider: str, entry_name: str) -> bool:
    requested = (provider or "").strip().lower()
    name = (entry_name or "").strip()
    if not requested or not name:
        return False
    return requested in {name.lower(), custom_provider_slug(name)}


def _model_matches_entry(model: str, entry: dict) -> bool:
    requested = (model or "").strip()
    if not requested:
        return False
    configured_model = str(entry.get("model", "") or "").strip()
    if requested == configured_model:
        return True
    models = entry.get("models") or {}
    if isinstance(models, dict) and requested in models:
        return True
    if isinstance(models, list) and requested in models:
        return True
    return False


def find_server_action(provider: str, model: str, custom_providers: list[dict] | None) -> str:
    if not custom_providers or not isinstance(custom_providers, list):
        return ""
    for entry in custom_providers:
        if not isinstance(entry, dict):
            continue
        if not _provider_matches_entry(provider, str(entry.get("name", "") or "")):
            continue
        if not _model_matches_entry(model, entry):
            continue
        return _safe_action(str(entry.get("server_action", "") or ""))
    return ""


def _switcher_path() -> Path:
    return Path(get_hermes_home()) / "use-local-model.sh"


def run_switcher_action(action: str, timeout: int = 240) -> LocalServerResult:
    cleaned = _safe_action(action)
    if not cleaned:
        raise ValueError(f"Unsafe local model server action: {action!r}")
    switcher = _switcher_path()
    proc = subprocess.run(
        [str(switcher), cleaned],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=True,
    )
    return LocalServerResult(True, cleaned, proc.stdout, proc.stderr)


def start_server_action(action: str) -> LocalServerResult:
    raw = action or ""
    cleaned = _safe_action(raw)
    if not cleaned:
        if str(raw).strip():
            raise ValueError(f"Unsafe local model server action: {action!r}")
        return LocalServerResult(False)
    result = run_switcher_action(cleaned)
    mark_active_server_action(cleaned)
    return result


def stop_active_local_server() -> bool:
    if not active_server_action():
        return False
    try:
        run_switcher_action("stop", timeout=120)
        return True
    finally:
        mark_active_server_action("")
