---
name: qa-record
description: Records observations, redacted evidence, cleanup and a verdict for a specific Agent-Relay QA case. Use after attempting a Q01 through Q10 variant, including when a prerequisite blocks it or the change is not in the verified build.
---

# Record one case

A result file is a report of observed behavior, not a prediction. Write one `<variant-id>.json`, for example `Q01-a.json`, inside the current run directory. This allows several variants of one case in the same run. The public Git repository is the permanent evidence record.

## Steps

1. Read `AGENTS.md`, the current `manifest.json`, the case definition, and the variant actually attempted. Confirm its expected outcome and the tester's observed outcome separately.
2. Record the start/observation times, actual waits or polling interval, provider request ID if safely pseudonymized, workspace status, status/metric deltas and direct observations. Use redacted excerpts only. A failed timeout is an observation, not a reason to mark a case blocked.
3. Choose exactly one verdict: `pass` when all required expectations were observed; `fail` when a required observation contradicted the case; `blocked` when a prerequisite prevented execution; `not-in-build` when the recorded relay revision does not contain the change. An unattempted variant remains unrun. Provide a concrete `reason` for every non-pass.
4. Record cleanup as a nonempty string, even if no workspace was created. If cleanup is pending, say so and do not claim the run is finished. Verify that the tester authorized any cleanup that changes resources.
5. Write a result file named exactly as the tested `variant_id`. Keep the `case_id` of its parent case. Evidence paths must refer only to files inside this run directory. Check every artifact for email, tokens, provider credentials, transcripts, private logs and screenshots before including it. Run `python3 scripts/validate.py`, fix errors, and inspect the diff.

## Example result

```json
{
  "case_id": "Q01",
  "variant_id": "Q01-a",
  "status": "pass",
  "observed_at": "2026-11-04T18:45:00Z",
  "observations": [
    "18:33:00Z request submitted; workspace became ready at 18:34:12Z after 72 seconds.",
    "18:35:00Z runner status was serving and the test prompt returned the expected response."
  ],
  "evidence": [],
  "cleanup": "QA workspace deleted at 18:42:00Z; no remaining containers observed."
}
```

This is an illustrative shape, not a completed test. Write actual facts, timestamps and identifiers for each run. Do not add a result for a variant you did not attempt.
