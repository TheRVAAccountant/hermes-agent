"""Regression coverage for the local ZAYA1 JANGTQ response path."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType


def _load_zaya_server_module():
    sys.modules.setdefault("jang_tools", ModuleType("jang_tools"))
    load_mod = ModuleType("jang_tools.load_jangtq")
    load_mod.load_jangtq_model = lambda *_args, **_kwargs: (object(), object())
    sys.modules["jang_tools.load_jangtq"] = load_mod
    mlx_lm_mod = ModuleType("mlx_lm")
    mlx_lm_mod.generate = lambda *_args, **_kwargs: ""
    sys.modules["mlx_lm"] = mlx_lm_mod

    server_path = Path.home() / ".hermes" / "serve-zaya1-jangtq4-server.py"
    spec = importlib.util.spec_from_file_location("zaya_jangtq_server_under_test", server_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_zaya_split_marks_unexecuted_action_plan_as_reasoning_only():
    server = _load_zaya_server_module()
    raw = "\n".join([
        "The user wants a list of all clients from the CRM.",
        "I need to find the CRM script or database and query it.",
        "I'll run the script to list clients.",
        "I'll check the output.",
        "I'll format the list.",
        "I'll provide the response.",
    ])

    split = server._split_generation(raw)

    assert split.status == "reasoning_only"
    assert split.content == ""
    assert "CRM" in split.reasoning


def test_zaya_completion_retries_reasoning_only_generation_with_thinking_disabled(monkeypatch):
    server = _load_zaya_server_module()
    calls = []

    class FakeTokenizer:
        def apply_chat_template(
            self,
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=True,
            tools=None,
        ):
            calls.append((tuple((m["role"], m["content"]) for m in messages), enable_thinking, tools))
            return "thinking-on" if enable_thinking else "thinking-off"

        def encode(self, text):
            return list(text or "x")

    outputs = iter([
        "The user wants a list.\nI'll run commands.\nI'll check output.\nI'll provide the response.",
        "No CRM query was run, so I cannot list clients from the provided context.",
    ])

    monkeypatch.setattr(server, "MODEL", object())
    monkeypatch.setattr(server, "TOKENIZER", FakeTokenizer())
    monkeypatch.setattr(server, "MODEL_ID", "zaya-test")
    monkeypatch.setattr(server, "generate", lambda *_args, **_kwargs: next(outputs))

    response = server._completion_response(
        [{"role": "user", "content": "List all the clients from the CRM"}],
        max_tokens=512,
    )

    message = response["choices"][0]["message"]
    assert message["content"].startswith("No CRM query was run")
    assert "I'll run commands" in message["reasoning_content"]
    assert response["jangtq_recovery"] == {"reasoning_only_retry": True, "retry_succeeded": True}
    assert calls[0][1] is True
    assert calls[1][1] is False
    assert "generated reasoning but no final answer" in calls[1][0][-1][1]


def test_zaya_completion_passes_tools_to_template_and_returns_tool_calls(monkeypatch):
    server = _load_zaya_server_module()
    calls = []

    class FakeTokenizer:
        def apply_chat_template(self, messages, **kwargs):
            calls.append((messages, kwargs))
            return "prompt"

        def encode(self, text):
            return list(text or "x")

    monkeypatch.setattr(server, "MODEL", object())
    monkeypatch.setattr(server, "TOKENIZER", FakeTokenizer())
    monkeypatch.setattr(server, "MODEL_ID", "zaya-test")
    monkeypatch.setattr(server, "generate", lambda *_args, **_kwargs: """<tool_call>
<function=terminal>
<parameter=command>
pwd
</parameter>
</function>
</tool_call>""")

    response = server._completion_response(
        [{"role": "user", "content": "run pwd"}],
        max_tokens=128,
        tools=[{"type": "function", "function": {"name": "terminal", "parameters": {}}}],
    )

    choice = response["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["content"] == ""
    assert choice["message"]["tool_calls"][0]["function"]["name"] == "terminal"
    assert json.loads(choice["message"]["tool_calls"][0]["function"]["arguments"]) == {"command": "pwd"}
    assert calls[0][1]["tools"][0]["type"] == "function"


def test_zaya_completion_parses_native_zyphra_tool_call(monkeypatch):
    server = _load_zaya_server_module()

    class FakeTokenizer:
        def apply_chat_template(self, messages, **kwargs):
            return "prompt"

        def encode(self, text):
            return list(text or "x")

    monkeypatch.setattr(server, "MODEL", object())
    monkeypatch.setattr(server, "TOKENIZER", FakeTokenizer())
    monkeypatch.setattr(server, "MODEL_ID", "zaya-test")
    monkeypatch.setattr(server, "generate", lambda *_args, **_kwargs: """<zyphra_tool_call>
<function=terminal>
<parameter=command>
pwd
</parameter>
</function>
</zyphra_tool_call>""")

    response = server._completion_response(
        [{"role": "user", "content": "run pwd"}],
        max_tokens=128,
        tools=[{"type": "function", "function": {"name": "terminal", "parameters": {}}}],
    )

    choice = response["choices"][0]
    assert choice["finish_reason"] == "tool_calls"
    assert choice["message"]["content"] == ""
    assert choice["message"]["tool_calls"][0]["function"]["name"] == "terminal"
    assert json.loads(choice["message"]["tool_calls"][0]["function"]["arguments"]) == {"command": "pwd"}
