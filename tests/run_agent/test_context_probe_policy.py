from run_agent import _should_probe_down_context_length


def test_openai_codex_does_not_guess_probe_tier_after_context_error():
    assert (
        _should_probe_down_context_length(
            provider="openai-codex",
            base_url="https://chatgpt.com/backend-api/codex",
        )
        is False
    )


def test_codex_backend_url_does_not_guess_probe_tier_without_provider():
    assert (
        _should_probe_down_context_length(
            provider="",
            base_url="https://chatgpt.com/backend-api/codex",
        )
        is False
    )


def test_local_custom_endpoint_still_uses_probe_tiers():
    assert (
        _should_probe_down_context_length(
            provider="custom:local-llamacpp",
            base_url="http://127.0.0.1:8080/v1",
        )
        is True
    )
