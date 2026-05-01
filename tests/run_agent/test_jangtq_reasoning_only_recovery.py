"""Regression coverage for Qwen JANGTQ reasoning-only failures.

The custom JANGTQ server lives in ~/.hermes rather than the Hermes repo, so
these tests import it directly with the heavy MLX/JANG modules stubbed out.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

from run_agent import AIAgent


def _load_jangtq_server_module():
    sys.modules.setdefault("jang_tools", ModuleType("jang_tools"))
    load_mod = ModuleType("jang_tools.load_jangtq")
    load_mod.load_jangtq_model = lambda *_args, **_kwargs: (object(), object())
    sys.modules["jang_tools.load_jangtq"] = load_mod
    mlx_lm_mod = ModuleType("mlx_lm")
    mlx_lm_mod.generate = lambda *_args, **_kwargs: ""
    sys.modules["mlx_lm"] = mlx_lm_mod

    server_path = Path.home() / ".hermes" / "serve-qwen36-jangtq4-server.py"
    spec = importlib.util.spec_from_file_location("jangtq_server_under_test", server_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_jangtq_split_marks_orphan_close_as_complete():
    server = _load_jangtq_server_module()

    split = server._split_generation("thinking steps</think>\n\nFinal answer.")

    assert split.status == "complete"
    assert split.reasoning == "thinking steps"
    assert split.content == "Final answer."


def test_jangtq_split_marks_untagged_action_plan_as_reasoning_only():
    server = _load_jangtq_server_module()
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


def test_jangtq_split_marks_numbered_thinking_process_as_reasoning_only():
    server = _load_jangtq_server_module()
    raw = "\n".join([
        "Here's a thinking process:",
        "1. **Understand User Request:** The user is asking to list clients from the CRM.",
        "2. **Identify Key Constraints/Context:** I do not have direct access to external systems.",
        "3. **Formulate Response Strategy:** Acknowledge the request and explain limitations.",
    ])

    split = server._split_generation(raw)

    assert split.status == "reasoning_only"
    assert split.content == ""
    assert "thinking process" in split.reasoning


def test_jangtq_demotes_post_think_planning_content():
    server = _load_jangtq_server_module()
    raw = "\n".join([
        "I need to think about the request.",
        "</think>",
        "The user wants the client list.",
        "I need to run the CRM script.",
        "I'll use the terminal tool.",
        "I'll check the output.",
        "I'll format the response.",
    ])

    split = server._split_generation(raw)

    assert split.status == "reasoning_only"
    assert split.content == ""
    assert "terminal tool" in split.reasoning


def test_jangtq_demotes_meta_review_plan_after_think():
    server = _load_jangtq_server_module()
    raw = "\n".join([
        "analysis text",
        "</think>",
        "4. Formulate Fixes:",
        "- Fix 1: Enforce stop sequences",
        "- Fix 2: Update parser",
        "- Fix 3: Add tests",
    ])

    split = server._split_generation(raw)

    assert split.status == "reasoning_only"
    assert split.content == ""


def test_jangtq_parses_single_xml_tool_call():
    server = _load_jangtq_server_module()
    raw = """Need to inspect the file.
<tool_call>
<function=read_file>
<parameter=path>
~/.hermes/config.yaml
</parameter>
</function>
</tool_call>"""

    parsed = server._parse_xml_tool_calls(raw)

    assert parsed.visible_content == ""
    assert len(parsed.tool_calls) == 1
    assert parsed.tool_calls[0]["type"] == "function"
    assert parsed.tool_calls[0]["function"]["name"] == "read_file"
    assert parsed.tool_calls[0]["function"]["arguments"] == '{"path": "~/.hermes/config.yaml"}'


def test_jangtq_completion_passes_tools_to_template_and_returns_tool_calls(monkeypatch):
    server = _load_jangtq_server_module()
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
            calls.append({"messages": messages, "enable_thinking": enable_thinking, "tools": tools})
            return "prompt"

        def encode(self, text):
            return list(text or "x")

    monkeypatch.setattr(server, "MODEL", object())
    monkeypatch.setattr(server, "TOKENIZER", FakeTokenizer())
    monkeypatch.setattr(server, "MODEL_ID", "jangtq-test")
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
    assert calls[0]["tools"][0]["type"] == "function"


def test_jangtq_preserves_tool_role_messages_for_template(monkeypatch):
    server = _load_jangtq_server_module()
    calls = []

    class FakeTokenizer:
        def apply_chat_template(self, messages, **kwargs):
            calls.append((messages, kwargs))
            return "prompt"

        def encode(self, text):
            return list(text or "x")

    monkeypatch.setattr(server, "MODEL", object())
    monkeypatch.setattr(server, "TOKENIZER", FakeTokenizer())
    monkeypatch.setattr(server, "MODEL_ID", "jangtq-test")
    monkeypatch.setattr(server, "generate", lambda *_args, **_kwargs: "Final answer.")

    server._completion_response(
        [
            {"role": "user", "content": "read file"},
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"path":"/tmp/x"}'},
                    }
                ],
            },
            {"role": "tool", "tool_call_id": "call_1", "content": "hello"},
        ],
        max_tokens=128,
    )

    messages = calls[0][0]
    assert messages[1]["role"] == "assistant"
    assert messages[1]["tool_calls"][0]["function"]["name"] == "read_file"
    assert messages[2]["role"] == "tool"
    assert messages[2]["content"] == "hello"


def test_local_provider_detects_numbered_thinking_process_as_unexecuted_plan():
    text = "\n".join([
        "Here's a thinking process:",
        "1. **Understand User Request:** The user is asking to list clients from the CRM.",
        "2. **Identify Key Constraints/Context:** I do not have direct access to external systems.",
        "3. **Formulate Response Strategy:** Acknowledge the request and explain limitations.",
    ])

    assert AIAgent._looks_like_unexecuted_action_plan(text) is True


def test_jangtq_completion_retries_reasoning_only_generation_with_thinking_disabled(monkeypatch):
    server = _load_jangtq_server_module()
    calls = []

    class FakeTokenizer:
        def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True, enable_thinking=True):
            calls.append((tuple((m["role"], m["content"]) for m in messages), enable_thinking))
            return "thinking-on" if enable_thinking else "thinking-off"

        def encode(self, text):
            return list(text or "x")

    outputs = iter([
        "The user wants a list.\nI'll run commands.\nI'll check output.\nI'll provide the response.",
        "No CRM query was run, so I cannot list clients from the provided context.",
    ])

    monkeypatch.setattr(server, "MODEL", object())
    monkeypatch.setattr(server, "TOKENIZER", FakeTokenizer())
    monkeypatch.setattr(server, "MODEL_ID", "jangtq-test")
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


def test_local_provider_detects_unexecuted_action_plan():
    with (
        patch("run_agent.get_tool_definitions", return_value=[]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key-1234567890",
            base_url="http://localhost:8093/v1",
            provider="custom",
            model="/Users/jeroncrooks/Qwen3.6-35B-A3B-JANGTQ4",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )

    plan = "\n".join([
        "The user wants a list of all clients from the CRM.",
        "I need to find the CRM script or database and query it.",
        "I'll run the script to list clients.",
        "I'll check the output.",
        "I'll format the list.",
        "I'll provide the response.",
    ])

    assert agent._looks_like_unexecuted_action_plan(plan) is True
    assert agent._looks_like_unexecuted_action_plan("Here are the clients: Alice, Bob.") is False


def test_local_provider_suppresses_unexecuted_action_plan_in_assistant_message():
    with (
        patch("run_agent.get_tool_definitions", return_value=[]),
        patch("run_agent.check_toolset_requirements", return_value={}),
        patch("run_agent.OpenAI"),
    ):
        agent = AIAgent(
            api_key="test-key-1234567890",
            base_url="http://localhost:8093/v1",
            provider="custom",
            model="/Users/jeroncrooks/Qwen3.6-35B-A3B-JANGTQ4",
            quiet_mode=True,
            skip_context_files=True,
            skip_memory=True,
        )

    plan = "\n".join([
        "The user wants a list of all clients from the CRM.",
        "I need to find the CRM script or database and query it.",
        "I'll run the script to list clients.",
        "I'll check the output.",
        "I'll format the list.",
        "I'll provide the response.",
    ])
    assistant_message = type(
        "AssistantMessage",
        (),
        {
            "content": plan,
            "tool_calls": None,
        },
    )()

    built = agent._build_assistant_message(assistant_message, "stop")

    assert built["content"] == (
        "Local model produced an unexecuted action plan instead of using tools. "
        "No tool-backed action was run."
    )
    assert "I'll run" not in built["content"]
