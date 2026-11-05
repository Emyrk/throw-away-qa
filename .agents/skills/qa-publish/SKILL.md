---
name: qa-publish
description: Validates and commits an Agent-Relay QA run to the repository's main branch. Use when a tester asks to publish recorded test results without a pull request.
---

# Publish a run

The owner authorized direct commits to `Emyrk/throw-away-qa` `refs/heads/main` only. Never apply that authorization to another repository or branch.

## Steps

1. Read `AGENTS.md`. This skill handles result commits **only after** the initial repository setup exists on remote `main`. Verify `git remote -v` names `Emyrk/throw-away-qa` and `git branch --show-current` is `main`. Run `git fetch origin main`, check `git status --short -b`, and inspect `git log --stat origin/main..HEAD`. If there are outgoing commits that are not authorized results from this run, stop; staging only a run directory would not prevent those commits from being pushed.
2. Run `python3 scripts/validate.py`. Inventory **every file** in the run directory, including unreferenced evidence. Inspect every text artifact and visually review every requested sanitized PNG for personal data, private URLs and secret-bearing pixels; validation only checks PNG structure, size and metadata. Ensure both the run and each attempted variant have chronologically ordered public-safe events with exact `at`, honest `time_basis`, and actual `recorded_at` values; a passing variant needs an event for every numbered step. Verify tested revision, observations, verdict and cleanup. Read the case expected outcomes again before claiming pass. A working tree containing someone else's edits is a blocker, not an invitation to stage them.
3. Stage **only** your run directory: `git add -- runs/<date>/<tester>/<run-id>/`. Inspect `git diff --cached --check`, `git diff --cached --stat` and the staged diff. Refuse to publish a secret or another tester's file. Commit with `test(qa): record <case IDs> <run ID>`; identify agent authorship in the commit body when applicable.
4. Fetch current `main`: `git fetch origin main`. If behind, `git rebase origin/main` on your unpublished commit. Compare each attempted `cases/Qxx.json` against the version at `suite_revision` in the run manifest. If any tested variant's expectations changed, stop for human reassessment; do not mechanically call the old pass valid. Run validation and review the **entire outgoing diff and file inventory** again. On a conflict stop and resolve it without discarding anyone's result; never force push or disable checks.
5. Recheck `git log --stat origin/main..HEAD`: every outgoing commit and file must belong to the authorized run. Push with the explicit ref `git push origin HEAD:refs/heads/main`. If another writer wins the race, fetch/rebase, recheck case expectations and the outgoing diff, validate, and retry once. If still rejected, report the blockage. Record the pushed commit SHA and case IDs. The static page will show committed results after its next build or local pull.

## Guardrails

- Do not amend or rewrite an already-published result; a correction is a new commit with the correction explained.
- The page and timers cannot attest completion. A case must have genuine observations and cleanup disposition.
- Do not modify the test definitions or Docker template as part of a results-only publication.
