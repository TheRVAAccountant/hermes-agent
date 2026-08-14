"""Focused tests for Z.AI model catalog behavior."""

from __future__ import annotations

from types import SimpleNamespace

from hermes_cli.models import _PROVIDER_MODELS, provider_model_ids, validate_requested_model


def test_zai_curated_catalog_includes_glm_53():
    assert _PROVIDER_MODELS["zai"][0] == "glm-5.3"
    assert "glm-5.2" in _PROVIDER_MODELS["zai"]


def test_zai_provider_model_ids_keeps_curated_latest_when_live_catalog_lags(monkeypatch):
    """Z.AI's live /models can lag DevPack docs; keep curated latest entries visible."""

    def fake_profile(_provider: str):
        return SimpleNamespace(
            auth_type="api_key",
            base_url="https://api.z.ai/api/coding/paas/v4",
            fallback_models=[],
            fetch_models=lambda api_key, base_url=None, **kwargs: [
                "glm-5.1",
                "glm-5",
                "glm-4.7",
            ],
        )

    monkeypatch.setattr("providers.get_provider_profile", fake_profile)
    monkeypatch.setattr(
        "hermes_cli.auth.resolve_api_key_provider_credentials",
        lambda provider_id: {
            "provider": provider_id,
            "api_key": "zai-test-key",
            "base_url": "https://api.z.ai/api/coding/paas/v4",
            "source": "ZAI_API_KEY",
        },
    )

    models = provider_model_ids("zai")

    assert models[0] == "glm-5.3"
    assert "glm-5.2" in models
    assert "glm-5.1" in models
    assert "glm-4.7" in models


def test_zai_model_validation_accepts_curated_latest_when_live_catalog_lags(monkeypatch):
    """Switching to GLM-5.3 should not warn just because live /models lags."""

    monkeypatch.setattr(
        "hermes_cli.models.fetch_api_models",
        lambda api_key, base_url, api_mode=None: ["glm-5.1", "glm-5", "glm-4.7"],
    )

    result = validate_requested_model(
        "glm-5.3",
        "zai",
        api_key="zai-test-key",
        base_url="https://api.z.ai/api/coding/paas/v4",
    )

    assert result["accepted"] is True
    assert result["persist"] is True
    assert result["recognized"] is True
    assert result["message"] is not None
    assert "curated catalog" in result["message"]
