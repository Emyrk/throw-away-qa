# Agent-Relay QA

A public, Git-backed manual QA suite for Agent-Relay on dogfood.cdr.dev. This repository holds the test cases, the Docker runner template source, a read-only HTML/JS viewer, and the results committed by testers' agents. A result is evidence of an observation, not an automated test assertion. No provider secrets or personal data belong here.

## Environment

QA runs use the `steven` organization and its Docker-capable provisioner. `templates/agent-relay-docker/` contains the **only** source for the proposed dual-provider QA runner template, including intentional failure parameters. `config/baseline.json` records proposed nonsecret relay and template settings. Confirm the live relay image/source revision, coderd version, template version, provider credentials, pool ownership, and each runner build's `image_digest` metadata before any run. The currently deployed dogfood relay may not contain every change represented by these cases; mark missing behavior `not-in-build`, not pass.

The cases cover the 36 PR merges on `coder/agent-relay` main in the rolling window 2026-10-05 17:20 UTC to 2026-11-04 17:20 UTC, grouped into ten workflows. Refresh the history and case coverage as new changes merge. Negative and fault-injection tests must target only QA resources and require explicit permission.

## View the suite

With Python 3.10+:

```sh
python3 scripts/validate.py
python3 scripts/build_site.py
python3 -m http.server 8000 --directory web
```

Open the local port 8000 through your Coder workspace app or browser. The page is read-only. It shows cases, configuration, timers, and committed results from generated `web/data.json`. That generated file is not a second source of truth; `cases/` and `runs/` are. The GitHub Pages workflow publishes the same static page from `main` **after the repository owner enables Pages in Settings > Pages and selects GitHub Actions as the build source**. Until then it validates and builds the site but skips deployment with a warning. After enabling, rerun the workflow or commit another result. This agent's GitHub integration cannot enable Pages itself. Check the displayed source revision before trusting a stale browser tab.

## Record a result

In your persistent tester workspace, clone this repository, read `AGENTS.md`, and ask your agent to use `qa-run` on a case ID. The agent records a unique `runs/<date>/<tester>/<run-id>/manifest.json`, then uses `qa-record` to save one `<variant-id>.json` per attempted variant with redacted evidence. The agent uses `qa-publish` to validate and commit its own run directly to this repository's `main`. No browser write API, database or result PR is required. Agents must never turn an unobserved condition into a pass.

The normal run sequence is:

1. Pin the case revision and inspect the actual QA environment.
2. Run a selected variant with timed steps and collect direct observations.
3. Record pass, fail, blocked or not-in-build, with reasons and cleanup.
4. Validate and inspect the public diff, then commit results to `main`.
5. Refresh the viewer after publication.

Only intentionally public, redacted evidence may be committed. Do not store emails, credentials, provider work orders, private logs or chat transcripts. The validator catches common leak patterns, but human review remains necessary.
