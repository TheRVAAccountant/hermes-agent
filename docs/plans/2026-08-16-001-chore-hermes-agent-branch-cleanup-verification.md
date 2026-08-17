# Hermes Agent Branch Cleanup Verification

Date: 2026-08-16
HEAD at receipt write: `chore/hermes-agent-branch-cleanup` @ `5dbd1d784` (inventory update pending on this same branch)
`main` / `origin/main`: `c0f89d254` (equal)
Park: `park/2026-08-16-host-experiments` @ `c37eb4e8b`

This receipt is on the chore branch only. It is not landed on `main`.

## AE1 — experiments parked off `main`

Given the untracked experiment roots, when park finished:

- `main` tree has no `plugins/familyops/`, `gateway/email_signature.py`, `hermes_cli/unload_models.py`, or `apps/desktop/electron/window-reopen.cjs`.
- The chore worktree also lacks those paths (empty leftover dirs removed).
- Those paths exist on `park/2026-08-16-host-experiments` (`git diff --name-only bab7be3ca c37eb4e8b`).
- `outputs/` stayed untracked. The 2026-08-16 plan stayed untracked.
- Live `.env` (not `.env.example`) is absent from `c37eb4e8b` and `5dbd1d784`.
- Park branch was not merged onto `main`.

Result: PASS

## AE2 — no unrelated-histories land

Feature tips still have no merge-base with `main` after bounded deepen (`--depth=50`, `200`, `500` of `origin/main` only).

Missing-parent SHAs were not cherry-picked: `14c4a849b`, `3cf8293e4`, `c896c09c4`, `972b16209`, `7e8f50a14`.

No `--allow-unrelated-histories`. No feature tip landed. `cursor/zai-glm53-profile-auth-1efe` and `feat/compound-engineering-skills` were not landed.

`main` moved only by fast-forward to `origin/main`. `bab7be3ca` remains an ancestor of `main`.

Result: PASS (deepen refused; default not-shippable held)

## AE3 — worktree hold

Sibling worktree `../hermes-agent-pr-55870` is clean on `chore/cron-profile-assignment` @ `bc60f1b41`.

The worktree was kept: the tip is not contained and is still unfinished cron-profile work. The branch was not force-deleted.

Result: PASS (held)

## AE4 — no push, Stage A, no restart

- `chore/hermes-agent-branch-cleanup` and `park/2026-08-16-host-experiments` have no remote tracking branch. `git ls-remote` for those names on `origin` and `fork` is empty.
- `openclaw-gateway`: `ActiveState=inactive`, `UnitFileState=enabled`. Not started, stopped, masked, or disabled.
- This run issued no Hermes gateway or Scholar restart.

Result: PASS

## Dispositions

| Branch | Disposition |
|---|---|
| `main` | Fast-forwarded to `origin/main` @ `c0f89d254`. Contains `bab7be3ca`. |
| `chore/hermes-agent-branch-cleanup` | experimental-parked (this-run docs). Not merged to `main`. |
| `park/2026-08-16-host-experiments` | experimental-parked. Never-land. |
| `chore/cron-profile-assignment` | worktree-hold. |
| `cursor/glm-5-3-zai-6531` | experimental-parked. needs-history. |
| `cursor/zai-glm53-profile-auth-1efe` | experimental-parked. needs-history. Do not land. |
| `feat/compound-engineering-skills` | experimental-parked. needs-history. Do not land. |
| `fix/cfo-zai-glm-5-3` | experimental-parked. needs-history. |
| `fix/remote-cron-profile-scope` | experimental-parked. needs-history. |

No local name was deleted: none were contained.

## End state vs plan DoD

Plan DoD asked for HEAD on `main`. Operator asked to do this run on `chore/hermes-agent-branch-cleanup` and not commit to `main` without a later yes.

End state: HEAD remains on the chore branch so the executing plan, inventory, and this receipt stay readable. `main` is clean of experiments and equals `origin/main`. Checkout of `main` is safe later; it will hide chore-only docs until those are merged.

## Follow-up (not this run)

- Unshallow this clone if recovered merge-bases are wanted.
- Operator accept of any recovered small patch.
- Yes-to-main before merging chore or park.
- Push only if the operator asks.
