---
name: qa-run
description: Sets up an Agent-Relay manual QA run and walks a selected test case. Use when a tester asks an agent to take Q01 through Q10 or start a new run.
---

# Start a QA run

Use one unique run directory per tester and environment revision. Keep the transient Agent-Relay runner workspace separate from the tester's persistent checkout of this repository.

## Steps

1. Read `AGENTS.md`, `README.md`, the selected `cases/Qxx.json`, and `config/baseline.json`. Confirm the user wants to run this case and has access to the named provider. Read each variant's prerequisites and cleanup before making changes.
2. Check `git status --short -b`, `git remote -v`, and `git fetch origin main`. Do not discard local work. Record the suite commit with `git rev-parse HEAD`; if behind, update safely before starting. Verify the target relay's running image digest/source SHA, coderd version, template version and image digest, module versions, and active pool config. If an item cannot be verified, name it in the run manifest and mark dependent cases blocked.
3. Identify the tester from an authenticated source, not a guessed login. Ask if necessary. Use a filename-safe tester slug and generate a UUID-based run ID. Create `runs/<UTC-date>/<tester>/<run-id>/manifest.json` with `run_id`, `tester`, `started_at` (UTC RFC3339), `suite_revision`, `relay_revision`, `organization: "steven"`, and known environment details. Add a timestamped `events` entry for the run's first observed action. Never store credentials or personal email.
4. Read the selected variant step by step with the tester. Present the exact configuration overlay and confirm it applies **only** to the QA pool. Capture baseline status/metrics with a UTC timestamp before triggering a provider request; append configuration, approvals and version snapshots to the run-level timeline. Ask before fault injection, deleting a workspace, changing a template version or restarting the QA relay.
5. Carry out observable checks. Capture the actual UTC time at **each** step transition, wait start/end, poll, provider request/claim, build state, runner state, user confirmation and cleanup. Retain a source and pseudonym for correlation. A timeout is a timestamped observation, not proof the system never acted. Do not backdate a tester's confirmation to the presumed reply time; mark it as a confirmation whose true occurrence is unknown.
6. At run end, set `ended_at` after the last observation and record cleanup/restoration events in the appropriate variant timeline. Hand the recorded events and outcome to `qa-record`. A run can contain results for one or more cases; do not fill other case results with guessed passes.

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
  "pool_config_hash": "<nonsecret config digest>",
  "events": [{
    "at": "2026-11-04T18:30:00Z",
    "recorded_at": "2026-11-04T18:30:00Z",
    "source": "operator",
    "kind": "run_started",
    "time_basis": "event",
    "summary": "The QA run began after checking the target revision."
  }]
}
```

Replace every example value with a real observation. If a value is unknown, write `unverified` and explain its consequence; do not create a fictional run.
