# Hermes Agent Branch Cleanup Inventory

Date: 2026-08-16
Checkout: this `hermes-agent` worktree
HEAD at inventory write: `chore/hermes-agent-branch-cleanup` @ `5dbd1d784`
Shallow: yes (deepen of `origin/main` stopped at `--depth=500`)

## Main vs remotes

| Ref | Tip | Note |
|---|---|---|
| `main` | `c0f89d254` | Fast-forwarded to `origin/main` after fetch. Still contains `bab7be3ca`. |
| `origin/main` | `c0f89d254` | Equal to local `main` after U2. |
| `main...origin/main` | 0 ahead, 0 behind | Fast-forward only. No merge commit. No drop of `bab7be3ca`. |

`origin` = `https://github.com/NousResearch/hermes-agent.git`
`fork` = `https://github.com/TheRVAAccountant/hermes-agent.git`
No push this run.

## Park set (committed on `park/2026-08-16-host-experiments` @ `c37eb4e8b`)

Never land this park branch onto `main`, even though it has a merge-base (`bab7be3ca`) and a small commit.

- Dirty MCP OAuth trio: `hermes_cli/web_routers/mcp.py`, `tests/tools/test_mcp_oauth.py`, `tools/mcp_oauth.py`
- `apps/desktop/electron/window-reopen.cjs`, `apps/desktop/electron/window-reopen.test.cjs`
- `gateway/email_signature.py`
- `hermes_cli/unload_models.py`
- `plugins/familyops/` including `.env.example` (no live `.env`)
- `tests/plugins/familyops/`
- `tests/gateway/test_sync_session_billing_route.py`
- `tests/hermes_cli/test_unload_models_command.py`
- `tests/run_agent/test_ollama_native_chat_bridge.py`
- `tests/test_validate_google_meet_setup.py`
- `tests/tools/test_discord_standalone_rate_limit.py`
- `tests/tools/test_send_message_email_signature.py`
- `tests/tools/test_skills_hub_collections.py`
- `tools/validate_google_meet_setup.py`
- Older plans: `docs/plans/2026-06-30-001-feat-compound-engineering-skills-plan.md`, `docs/plans/2026-06-30-002-fix-voice-transcription-cuda-fallback-plan.md`, `docs/plans/2026-08-14-001-fix-gateway-skew-branch-cleanup-plan.md`, `docs/plans/2026-08-14-001-fix-gateway-skew-branch-cleanup-verification.md`

After park, `main` and this chore branch trees do not contain familyops, email-signature, unload-models, or window-reopen files.

## Never-commit (left untracked)

- `outputs/` (`google-meet-setup-secret-scan.json`, `google-meet-setup-validation-report.md`, `google-meet-setup-validation.json`)
- Any file named `.env` that is not `.env.example` (none found)

## Keep readable in this worktree (untracked, not parked)

- `docs/plans/2026-08-16-001-chore-hermes-agent-branch-cleanup-plan.md`
- This inventory, after it is committed on `chore/hermes-agent-branch-cleanup` only

## Local branch rows

Labels: `contained` | `needs-history` | `experimental` | `worktree-hold` | `shippable`.
`shippable` only after a merge-base exists and the operator accepts the patch.

| Branch | Tip | Merge-base with `main` | Label | Disposition |
|---|---|---|---|---|
| `main` | `c0f89d254` | self | land-target | Equals `origin/main`. Contains `bab7be3ca`. |
| `chore/hermes-agent-branch-cleanup` | `5dbd1d784` | `bab7be3ca` | experimental | This-run execution branch. Do not merge onto `main` unless the operator later says yes. |
| `park/2026-08-16-host-experiments` | `c37eb4e8b` | `bab7be3ca` | experimental | Never-land. Holds host experiments and dirty MCP OAuth edits. |
| `chore/cron-profile-assignment` | `bc60f1b41` | none | worktree-hold + needs-history | Held by sibling worktree `hermes-agent-pr-55870`. Unique chain `bc60f1b41` → `2228c2e6c` → `14c4a849b` (parent missing). |
| `cursor/glm-5-3-zai-6531` | `4c4c84b38` | none | experimental + needs-history | `/model` space form. Unique chain `4c4c84b38` → `cd87a95dd` → `3cf8293e4` (parent missing). |
| `cursor/zai-glm53-profile-auth-1efe` | `7e5f79c28` | none | experimental + needs-history | Includes `chore: park dirty host edits`. Do not land. Unique chain ends at `c896c09c4` (parent missing). |
| `feat/compound-engineering-skills` | `972b16209` | none | experimental + needs-history | Stale merge tip `#55410`. Parent missing. Do not land. |
| `fix/cfo-zai-glm-5-3` | `c896c09c4` | none | needs-history | Desktop spawn. Shallow-root; parent missing. |
| `fix/remote-cron-profile-scope` | `082b73182` | none | needs-history | Desktop cron routing. Unique chain `082b73182` → `7e8f50a14` (parent missing). |

No row is `shippable`. No feature tip is `contained` after the `main` fast-forward.

## U2 deepen result

Fetched `origin main` only (no pull, no `--unshallow`, no `--deepen`, no `cli.py` `_deepen_shallow_repo`).

| Depth | `origin/main` tip | Feature merge-bases vs `main` |
|---|---|---|
| before | `f0ab10455` (count 1) | none |
| `--depth=50` | `8dc427949` (count 50) | none |
| `--depth=200` | `c0f89d254` (count 308) | none |
| `--depth=500` | `c0f89d254` (count 637) | none |

Deepen refused. Missing-parent SHAs still have no parent objects. No cherry-pick. No land. Park branch not landed.

## Missing-parent SHAs (do not cherry-pick)

`14c4a849b`, `3cf8293e4`, `c896c09c4`, `972b16209`, `7e8f50a14`

## Parent-present incremental commits (still not shippable)

`2228c2e6c`, `bc60f1b41`, `4c4c84b38`, `cd87a95dd`, `7e5f79c28`, `ea19ccf87`, `178897a6c`, `082b73182`

## Worktrees

| Path | HEAD | Branch | Status |
|---|---|---|---|
| this checkout | `5dbd1d784` | `chore/hermes-agent-branch-cleanup` | Primary. Untracked: this-run plan, `outputs/`. |
| `../hermes-agent-pr-55870` | `bc60f1b41` | `chore/cron-profile-assignment` | Clean. Do not force-delete the branch while this worktree holds it. |

## Stage A

`openclaw-gateway`: inactive + enabled. Do not start, stop, mask, or disable.
No Hermes or Scholar restart. No remote push.
