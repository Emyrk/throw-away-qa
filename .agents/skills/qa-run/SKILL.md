---
name: qa-run
description: Sets up an Agent-Relay manual QA run and walks a selected test case. Use when a tester asks an agent to take Q01 through Q10 or start a new run.
---

# Start a QA run

Use one unique run directory per tester and environment revision. Keep the transient Agent-Relay runner workspace separate from the tester's persistent checkout of this repository.

## Steps

1. Read `AGENTS.md`, `README.md`, the selected `cases/Qxx.json`, and `config/baseline.json`. Confirm the user wants to run this case and has access to the named provider. Read each variant's prerequisites and cleanup before making changes.
2. Check `git status --short -b`, `git remote -v`, and `git fetch origin main`. Do not discard local work. Record the suite commit with `git rev-parse HEAD`; if behind, update safely before starting. Verify the target relay's running image digest/source SHA, coderd version, template version and image digest, module versions, and active pool config. If an item cannot be verified, name it in the run manifest and mark dependent cases blocked.
3. Identify the tester from an authenticated source, not a guessed login. Ask if necessary. Use a filename-safe tester slug and generate a UUID-based run ID. Create `runs/<UTC-date>/<tester>/<run-id>/manifest.json` with `run_id`, `tester`, `started_at` (UTC ISO 8601), `suite_revision`, `relay_revision`, `organization: "steven"`, and known environment details. Never store credentials or personal email.
4. Read the selected variant step by step with the tester. Present the exact configuration overlay and confirm it applies **only** to the QA pool. Capture a baseline status/metrics snapshot before triggering a provider request. Ask before fault injection, deleting a workspace, changing a template version or restarting the QA relay.
5. Carry out observable checks. Wait and poll for the intervals in the case, recording actual UTC times rather than assuming a condition happened on schedule. If the condition does not occur by its timeout, record that observation and continue to cleanup. Ask the tester to confirm UI observations the agent cannot inspect directly.
6. Hand observations to `qa-record`. A run can contain results for one or more cases. Do not fill other case results with guessed passes.

## Example manifest

```json
{
  "run_id": "bda3f454-4240-4d95-8bb8-80c900706412",
  "tester": "tester-handle",
  "started_at": "2026-11-04T18:30:00Z",
  "suite_revision": "<git commit SHA>",
  "relay_revision": "<running image source SHA or unverified>",
  "organization": "steven",
  "template_version": "<recorded template version>",
  "pool_config_hash": "<nonsecret config digest>"
}
```

Replace every example value with a real observation. If a value is unknown, write `unverified` and explain its consequence; do not create a fictional run.
