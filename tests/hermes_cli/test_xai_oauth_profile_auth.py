"""Regression tests for xAI OAuth auth resolution in profile/cron contexts."""

import base64
import json
import time

import pytest

from hermes_cli import auth
from hermes_cli.auth import AuthError


def _jwt_with_exp(exp_epoch: int) -> str:
    """Build a minimal JWT-shaped string with the given exp claim."""
    payload = {"exp": exp_epoch}
    encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8"))
        .rstrip(b"=")
        .decode("utf-8")
    )
    return f"h.{encoded}.s"


def test_read_xai_oauth_tokens_uses_credential_pool_when_provider_tokens_empty(monkeypatch):
    """Profile auth can have fresh pool tokens while singleton provider state is empty.

    This mirrors profiled cron after re-auth/credential-pool sync: the xAI
    OAuth credential is usable, but `providers.xai-oauth.tokens` may be empty
    or stale. Treating that as missing auth makes cron keep failing after the
    user has successfully re-authenticated.
    """
    store = {
        "providers": {"xai-oauth": {"tokens": {}, "last_auth_error": {}}},
        "credential_pool": {
            "xai-oauth": [
                {
                    "access_token": "pool-access",
                    "refresh_token": "pool-refresh",
                    "token_type": "Bearer",
                    "last_refresh": "2026-06-03T19:00:00Z",
                }
            ]
        },
    }
    monkeypatch.setattr(auth, "_load_auth_store", lambda: store)
    monkeypatch.setattr(auth, "_load_global_auth_store", lambda: {})

    resolved = auth._read_xai_oauth_tokens(_lock=False)

    assert resolved["tokens"]["access_token"] == "pool-access"
    assert resolved["tokens"]["refresh_token"] == "pool-refresh"
    assert resolved["tokens"]["token_type"] == "Bearer"
    assert resolved["last_refresh"] == "2026-06-03T19:00:00Z"


def test_read_xai_oauth_tokens_skips_dead_first_pool_entry_when_singleton_empty(monkeypatch):
    """Post-quarantine stores keep a dead pool head in front of a live grant.

    ``_xai_oauth_state_from_store`` used to return the first pool row with
    any access+refresh pair. After a singleton ``invalid_grant`` quarantine,
    that head is the revoked Aug-13 grant; the live rotated grant sits
    behind it. ``/model`` then refreshes the dead head and fails even though
    a usable token is already in the pool.
    """
    now = int(time.time())
    expired = _jwt_with_exp(now - 3600)
    live = _jwt_with_exp(now + 3600)
    store = {
        "providers": {
            "xai-oauth": {
                "tokens": {"token_type": "Bearer"},
                "last_auth_error": {"relogin_required": True, "code": "xai_refresh_failed"},
            }
        },
        "credential_pool": {
            "xai-oauth": [
                {
                    "access_token": expired,
                    "refresh_token": "dead-pool-refresh",
                    "token_type": "Bearer",
                    "last_refresh": "2026-08-13T03:04:36Z",
                },
                {
                    "access_token": live,
                    "refresh_token": "live-pool-refresh",
                    "token_type": "Bearer",
                    "last_refresh": "2026-08-17T04:19:42Z",
                },
            ]
        },
    }
    monkeypatch.setattr(auth, "_load_auth_store", lambda: store)
    monkeypatch.setattr(auth, "_load_global_auth_store", lambda: {})

    resolved = auth._read_xai_oauth_tokens(_lock=False)

    assert resolved["tokens"]["refresh_token"] == "live-pool-refresh"
    assert resolved["last_refresh"] == "2026-08-17T04:19:42Z"


def test_read_xai_oauth_tokens_prefers_live_pool_over_expired_singleton(monkeypatch):
    """A live pool grant must win over an expired singleton that still has tokens.

    The Telegram ``/model`` picker uses ``credential_pool.select()``, which
    can lease a non-expired pool entry. The switch path used
    ``_read_xai_oauth_tokens``, which preferred the singleton whenever both
    token fields were present — even when that access JWT was already dead.
    Selecting Grok then refreshed the revoked singleton and surfaced
    ``invalid_grant`` while a valid SuperGrok grant sat in the pool.
    """
    now = int(time.time())
    expired = _jwt_with_exp(now - 3600)
    live = _jwt_with_exp(now + 3600)
    store = {
        "providers": {
            "xai-oauth": {
                "tokens": {
                    "access_token": expired,
                    "refresh_token": "dead-singleton-refresh",
                    "token_type": "Bearer",
                },
                "last_refresh": "2026-08-13T02:53:15Z",
            }
        },
        "credential_pool": {
            "xai-oauth": [
                {
                    "access_token": expired,
                    "refresh_token": "dead-pool-refresh",
                    "token_type": "Bearer",
                    "last_refresh": "2026-08-13T03:04:36Z",
                },
                {
                    "access_token": live,
                    "refresh_token": "live-pool-refresh",
                    "token_type": "Bearer",
                    "last_refresh": "2026-08-17T04:19:42Z",
                },
            ]
        },
    }
    monkeypatch.setattr(auth, "_load_auth_store", lambda: store)
    monkeypatch.setattr(auth, "_load_global_auth_store", lambda: {})

    resolved = auth._read_xai_oauth_tokens(_lock=False)

    assert resolved["tokens"]["refresh_token"] == "live-pool-refresh"
    assert not auth._xai_access_token_is_expiring(resolved["tokens"]["access_token"], 0)


def test_resolve_xai_oauth_runtime_credentials_does_not_refresh_dead_singleton_when_pool_is_live(
    monkeypatch,
):
    """Switching to xAI must not POST the revoked singleton when a live pool JWT exists."""
    now = int(time.time())
    expired = _jwt_with_exp(now - 3600)
    live = _jwt_with_exp(now + 8 * 3600)
    store = {
        "providers": {
            "xai-oauth": {
                "tokens": {
                    "access_token": expired,
                    "refresh_token": "dead-singleton-refresh",
                    "token_type": "Bearer",
                },
                "last_refresh": "2026-08-13T02:53:15Z",
            }
        },
        "credential_pool": {
            "xai-oauth": [
                {
                    "access_token": live,
                    "refresh_token": "live-pool-refresh",
                    "token_type": "Bearer",
                    "last_refresh": "2026-08-17T04:19:42Z",
                },
            ]
        },
    }
    monkeypatch.setattr(auth, "_load_auth_store", lambda: store)
    monkeypatch.setattr(auth, "_load_global_auth_store", lambda: {})

    def _must_not_refresh(*_args, **_kwargs):
        raise AssertionError("must not refresh the dead singleton when a live pool grant exists")

    monkeypatch.setattr(auth, "_refresh_xai_oauth_tokens", _must_not_refresh)

    creds = auth.resolve_xai_oauth_runtime_credentials()

    assert creds["api_key"] == live
    assert creds["provider"] == "xai-oauth"


