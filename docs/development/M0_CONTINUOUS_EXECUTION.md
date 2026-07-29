# RECA M0 Continuous Execution

## Branch and pull request

- Continuous development branch: `codex/m0-continuous`
- One Draft pull request is maintained from `codex/m0-continuous` to `main`.
- M0 stage branches are not merged to `main` during continuous development.

## Checkpoints and commits

Each completed stage has one scoped commit and a non-overwriting checkpoint tag
such as `m0-01-checkpoint` through `m0-08-checkpoint` and
`m0-fix-checkpoint`. A checkpoint is a code snapshot, not an acceptance PASS.

## Non-interruption policy

External service outages, local tooling gaps, and non-critical test failures do
not stop unrelated safe work. They are recorded in the M0 issue register with
evidence, severity, workaround, and a planned resolution target. Security,
data-loss, license, provenance, secret, and fixed-version violations are never
worked around by weakening controls.

## Issue register and recovery

`docs/acceptance/M0_ISSUE_REGISTER.md` is the sole M0 issue ledger. Existing
issue IDs are updated rather than duplicated. If unrelated user changes make a
worktree unsafe, preserve them in a timestamped stash and record its reference
before continuing.

## Final repair and merge

M0-FIX consolidates all open issues. Only after M0 final review passes may the
Draft pull request be merged and `m0-complete` be created. No force-push or
rewriting of pushed continuous-branch history is permitted.
