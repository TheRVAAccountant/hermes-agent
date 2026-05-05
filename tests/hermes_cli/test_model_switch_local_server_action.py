from hermes_cli.model_switch import switch_model


MODEL_PATH = "/Users/jeroncrooks/Qwen3.6-35B-A3B-JANGTQ4"


def test_switch_model_starts_custom_provider_server_action_before_validation(monkeypatch):
    calls = []
    custom_providers = [
        {
            "name": "local-mlx-qwen36-jangtq4",
            "base_url": "http://localhost:8093/v1",
            "model": MODEL_PATH,
            "models": {MODEL_PATH: {"context_length": 262144}},
            "server_action": "qwen36jangtq",
        }
    ]

    def fake_runtime_provider(**kwargs):
        return {
            "provider": "custom:local-mlx-qwen36-jangtq4",
            "api_key": "no-key-required",
            "base_url": "http://localhost:8093/v1",
            "api_mode": "chat_completions",
        }

    def fake_start_server_action(action):
        calls.append(("start", action))

    def fake_validate(*args, **kwargs):
        calls.append(("validate", args, kwargs))
        return {"accepted": True, "persist": True, "recognized": True}

    monkeypatch.setattr(
        "hermes_cli.runtime_provider.resolve_runtime_provider",
        fake_runtime_provider,
    )
    monkeypatch.setattr(
        "hermes_cli.local_model_servers.start_server_action",
        fake_start_server_action,
    )
    monkeypatch.setattr(
        "hermes_cli.models.validate_requested_model",
        fake_validate,
    )
    monkeypatch.setattr(
        "hermes_cli.model_switch.get_model_capabilities",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        "hermes_cli.model_switch.get_model_info",
        lambda *args, **kwargs: None,
    )

    result = switch_model(
        MODEL_PATH,
        current_provider="openrouter",
        current_model="openai/gpt-5",
        explicit_provider="custom:local-mlx-qwen36-jangtq4",
        custom_providers=custom_providers,
    )

    assert result.success is True
    assert calls[0] == ("start", "qwen36jangtq")
    assert calls[1][0] == "validate"
