from pathlib import Path
import subprocess

import pytest

from hermes_cli.local_model_servers import (
    find_server_action,
    mark_active_server_action,
    active_server_action,
    start_server_action,
    stop_active_local_server,
)


MODEL_PATH = "/Users/jeroncrooks/.cache/lm-studio/models/mlx-community/gemma-4-26b-a4b-it-4bit"


def _providers():
    return [
        {
            "name": "local-mlx-gemma4-4bit",
            "base_url": "http://localhost:8092/v1",
            "model": MODEL_PATH,
            "models": {MODEL_PATH: {"context_length": 262144}},
            "server_action": "gemmamlx",
        }
    ]


def test_find_server_action_for_named_custom_provider_and_model():
    assert find_server_action("custom:local-mlx-gemma4-4bit", MODEL_PATH, _providers()) == "gemmamlx"


def test_find_server_action_rejects_unsafe_action():
    providers = _providers()
    providers[0]["server_action"] = "gemmamlx; rm -rf /"

    assert find_server_action("custom:local-mlx-gemma4-4bit", MODEL_PATH, providers) == ""


def test_start_server_action_calls_switcher(monkeypatch, tmp_path):
    calls = []

    switcher = tmp_path / "use-local-model.sh"
    switcher.write_text("#!/usr/bin/env bash\n", encoding="utf-8")

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, stdout="started", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = start_server_action("gemmamlx")

    assert result.ran is True
    assert result.action == "gemmamlx"
    assert calls[0][0] == [str(switcher), "gemmamlx"]
    assert calls[0][1]["check"] is True


def test_stop_active_local_server_only_stops_when_active(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "hermes_cli.local_model_servers.run_switcher_action",
        lambda action, timeout=120: calls.append((action, timeout)) or object(),
    )

    mark_active_server_action("")
    assert stop_active_local_server() is False
    assert calls == []

    mark_active_server_action("gemmamlx")
    assert active_server_action() == "gemmamlx"
    assert stop_active_local_server() is True
    assert calls == [("stop", 120)]
    assert active_server_action() == ""


def test_start_server_action_rejects_unsafe_action():
    with pytest.raises(ValueError):
        start_server_action("gemmamlx && say nope")
