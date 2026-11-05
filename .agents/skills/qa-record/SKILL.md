---
name: qa-record
description: Records observations, redacted evidence, cleanup and a verdict for a specific Agent-Relay QA case. Use after attempting a Q01 through Q10 variant, including when a prerequisite blocks it or the change is not in the verified build.
---

# Record one case

A result file is a report of observed behavior, not a prediction. Write one `<variant-id>.json`, for example `Q01-a.json`, inside the current run directory. This allows several variants of one case in the same run. The public Git repository is the permanent evidence record.

## Steps

1. Read `AGENTS.md`, the current `manifest.json`, the case definition, and the variant actually attempted. Confirm its expected outcome and the tester's observed outcome separately.
2. Build an ordered `events` array from each observable step and transition, including UTC time, source, event kind, time basis, short public-safe summary, numbered `step` when relevant, and a pseudonymous `subject` for related workspaces. Record `recorded_at` separately; if an event is added later from private logs, preserve the log's exact `at` and use the actual backfill time as `recorded_at`. Use `time_basis: "observation"` when occurrence time is unknown and `"confirmation"` for a tester's later attestation; never pretend either is the provider's response timestamp. Capture wait start/end, poll samples, metric values, configuration changes, claims/nacks, build/agent/runner state, reply confirmation, failures, and cleanup where observed. Narrative `observations` should summarize conclusions, not repeat the timeline. Use redacted excerpts only.
3. Choose exactly one verdict: `pass` when all required expectations were observed; `fail` when a required observation contradicted the case; `blocked` when a prerequisite prevented execution; `not-in-build` when the recorded relay revision does not contain the change. An unattempted variant remains unrun. Provide a concrete `reason` for every non-pass.
4. Record cleanup as a nonempty string, even if no workspace was created. If cleanup is pending, say so and do not claim the run is finished. Verify that the tester authorized any cleanup that changes resources.
5. Write a result file named exactly as the tested `variant_id`. Keep the `case_id` of its parent case. Passing results need at least one event for **each numbered step**; blocked results still need a timestamped blocking event. Evidence paths must refer only to files inside this run directory. Check every artifact for email, tokens, provider credentials, transcripts and private logs. Include a screenshot only when requested: inspect the actual pixels, remove text and EXIF metadata, use a small PNG, and reference its relative path. Run `python3 scripts/validate.py`, fix errors, and inspect the diff.

## Example result

```json
{
  "case_id": "Q01",
  "variant_id": "Q01-a",
  "status": "pass",
  "observed_at": "2026-11-04T18:45:00Z",
  "observations": ["The workspace became ready and the tester confirmed a reply."],
  "events": [
    {"at": "2026-11-04T18:33:00Z", "recorded_at": "2026-11-04T18:33:00Z", "source": "tester", "kind": "prompt_submitted", "time_basis": "observation", "step": 1, "subject": "claude-a", "summary": "The tester submitted a QA prompt; the exact provider receipt time is unknown."},
    {"at": "2026-11-04T18:34:12.123456Z", "recorded_at": "2026-11-04T18:34:13Z", "source": "relay_log", "kind": "runner_handoff", "time_basis": "event", "step": 2, "subject": "claude-a", "summary": "The workspace built and the runner handoff completed."},
    {"at": "2026-11-04T18:35:00Z", "recorded_at": "2026-11-04T18:35:00Z", "source": "tester", "kind": "reply_confirmed", "time_basis": "confirmation", "step": 2, "subject": "claude-a", "summary": "The tester confirmed a visible reply; its exact completion time is unknown."},
    {"at": "2026-11-04T18:42:00Z", "recorded_at": "2026-11-04T18:42:05Z", "source": "coder_api", "kind": "cleanup_verified", "time_basis": "observation", "subject": "claude-a", "summary": "The disposable QA workspace was absent from the Coder listing."}
  ],
  "evidence": [],
  "cleanup": "QA workspace deleted at 18:42:00Z; no remaining containers observed."
}
```

This is an illustrative shape, not a completed test. Write actual facts, timestamps and identifiers for each run. Do not add a result for a variant you did not attempt.
