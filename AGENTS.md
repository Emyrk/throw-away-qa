# Agent-Relay QA agents

This public repository is the test plan and the evidence of executed tests. The HTML page is a read-only view of files in Git. Agents, not the browser, record results.

## Start here

1. Read this file, then `README.md` and the selected `cases/Qxx.json` before taking a case.
2. Use `.agents/skills/qa-run/SKILL.md` to establish a run, `.agents/skills/qa-record/SKILL.md` for each case, and `.agents/skills/qa-publish/SKILL.md` to share results.
3. Check the Git remote and branch, the tested relay image/source revision, coderd version, template version, and pool configuration. Never infer that a recently merged change is deployed.
4. Use organization `steven`. The Docker provisioner and runner template are QA resources; do not modify production pools, templates, provisioners, or users.

## Evidence integrity

- Record exactly what happened, with UTC timestamps and actual waits. A timer ending, a script exiting, or an agent's expectation is not a manual pass.
- Link each result to a case definition and test variant. Keep facts distinct from hypotheses. If a case cannot run, mark it `blocked` or `not-in-build` with a reason; do not fabricate steps.
- Make each tester's run directory unique: `runs/YYYY-MM-DD/<tester>/<run-id>/`. Change only your own run files. Do not overwrite anyone else's results or silently rewrite published evidence.
- Every run manifest and attempted variant must contain an ordered `events` timeline. For each event record `at` (UTC RFC3339 occurrence or observation time), `recorded_at` (when written), `source`, `kind`, `time_basis`, and a redacted `summary`; use `step` for case steps and a short `subject` pseudonym to correlate repeated workspaces. `time_basis` is `event` for a sourced occurrence, `observation` when only the observation time is known, or `confirmation` when a tester later confirms an earlier outcome. Preserve subsecond precision from source timestamps. Never invent an exact time: when the occurrence is unknown, use the actual observation or confirmation time and say so in the summary.
- Record each configuration change, approval, prompt or queue event, claim, build state, agent/runner transition, poll/metric sample, provider outcome, timeout and cleanup when observed. For passing variants, timestamp evidence for every numbered step. Keep these structured events as the canonical timeline; narrative observations summarize the outcome rather than duplicating the entire event list.
- Every case result requires a final verdict, observations, a timeline and cleanup disposition. The `qa-record` skill shows the file shape. Cases that were not attempted need no result file and display as unrun.
- This repository is public. Do not commit passwords, session tokens, provider secrets, raw work orders, chat transcripts, owner emails, private logs, unredacted screenshots or any binary evidence that cannot be reviewed as text. Prefer counts, status codes, timestamps, pseudonymous IDs and redacted excerpts. Inventory **all** files in your run, even if a result does not reference them. Inspect evidence manually as well as running `python3 scripts/validate.py`.
- Destructive fault injection, changing live provider pools, removing workspaces, and altering the relay deployment require explicit authorization for that action. Safe observation does not authorize disruption.

## Publishing

The owner explicitly allowed results and the initial setup to be committed to `Emyrk/throw-away-qa` `refs/heads/main` without pull requests. The initial setup is a separate reviewed commit procedure; `qa-publish` is only for results after that baseline exists on remote `main`. Before any commit or push, verify the actual Git remote and branch, inspect the full outgoing commit range and working tree, and run validation. Never force-push or bypass a failing check. This permission applies only to this QA repository, not the source repositories or dogfood infrastructure.

Template source lives only under `templates/agent-relay-docker/`. Do not copy secrets or provisioner host credentials into template files. The HTML/JS app reads generated data; update case definitions and results instead of copying case prose into the UI. Every case and variant needs a one- or two-sentence human-readable `summary` that says what it checks, distinct from its detailed steps. To prepare a local relay, use `scripts/prepare-relay-config.py`, `scripts/run-relay.sh` and `scripts/check-relay.sh`; never print environment variable values or commit private logs.
