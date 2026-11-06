# Agent-Relay QA

A public, Git-backed manual QA suite for Agent-Relay on dogfood.cdr.dev. This repository holds the test cases, the Docker runner template source, a read-only HTML/JS viewer, and the results committed by testers' agents. A result is evidence of an observation, not an automated test assertion. No provider secrets or personal data belong here.

## Environment

QA runs use the `steven` organization and its Docker-capable provisioner. `templates/agent-relay-docker/` contains the **only** source for the dual-provider QA runner template, including intentional failure parameters. `config/baseline.json` records the nonsecret workspace-local relay and template settings; it is not a substitute for checking the running process. Confirm the live relay binary/source revision, coderd version, template version, provider pool ownership, and each runner build's `image_digest` metadata before any run. The currently deployed dogfood relay may not contain every change represented by these cases; mark missing behavior `not-in-build`, not pass.

The cases cover the 36 PR merges on `coder/agent-relay` main in the rolling window 2026-10-05 17:20 UTC to 2026-11-04 17:20 UTC, grouped into ten workflows. Refresh the history and case coverage as new changes merge. Negative and fault-injection tests must target only QA resources and require explicit permission.

## Run the QA relay in a tester workspace

Build from a pinned `coder/agent-relay` source revision, not from the older dogfood image. In this workspace, the local QA binary is built from `23e85405e923e153baf2eb2ecab5576b3690c273` at `~/.local/bin/agent-relay-qa`. Run `python3 scripts/prepare-relay-config.py` once to render `~/.config/agent-relay-qa/config.yaml` (mode 0600) from `config/baseline.json`. The renderer refuses to overwrite a local overlay and rejects an inline pool secret. Its listeners use loopback ports **22112** (metrics and `/readyz`) and **22113** (token-authenticated status page), because 2112 and 2113 are occupied in this workspace. The config file is JSON syntax accepted as YAML by the relay and contains no credentials.

Before starting, confirm `qa-claude` and Cursor's `steven-agent-relay` are distinct, QA-only provider queues, and verify that the relay service account belongs to `steven` with the required permissions. Make these **three** values available as environment variables to the Relay process: `CODER_AGENT_RELAY_CODERD_SESSION_TOKEN`, `QA_CLAUDE_POOL_SECRET`, and `QA_CURSOR_SERVICE_ACCOUNT_KEY`. This workspace has a private, mode-0600 skeleton at `~/.config/agent-relay-qa/secrets.env`; fill its shell assignments in a workspace editor, **not in chat or Git**. The start script checks ownership and mode before loading it, and also accepts securely injected environment variables. The Coder token must be a dedicated relay service-account token, not the interactive workspace `CODER_SESSION_TOKEN`. No secret values are printed or written by the scripts. Do not enable dangerous parameter credential transport.

When the QA-only queues and credentials are confirmed, set `AGENT_RELAY_QA_POOLS_CONFIRMED=yes` in the Relay process environment and run `sh scripts/run-relay.sh`. It writes logs to the private workspace path `~/.config/agent-relay-qa/relay.log`, not to this public repo. Run `sh scripts/check-relay.sh` to inspect `/readyz`, labeled pool health and status listener liveness. Readiness 200 means **at least one** pool is healthy, so check both labeled pool gauges. For the status UI, use a separate short-lived Coder reader token with workspace-read access; do not sign in with the Relay service-account token or the workspace's existing interactive session token. Do not copy raw logs or credential-bearing API output into public result evidence. The relay is not started automatically by the suite.

## View the suite

With Python 3.10+:

```sh
python3 scripts/validate.py
python3 scripts/build_site.py
python3 -m http.server 8000 --directory web
```

Open the local port 8000 through your Coder workspace app or browser. The read-only page shows each latest tested variant as **Tried / Happened / Wanted**, with reviewed screenshots only where available. `RESULTS.md` supplies the short wording; validated files in `runs/` supply the latest verdicts and images. `web/data.json` is generated, not a second source of truth. The GitHub Pages workflow publishes the static page from `main`.

## Record a result

In your persistent tester workspace, clone this repository, read `AGENTS.md`, and ask your agent to use `qa-run` on a case ID. The agent records a unique `runs/<date>/<tester>/<run-id>/manifest.json`, then uses `qa-record` to save one `<variant-id>.json` per attempted variant with a detailed public-safe UTC event timeline and redacted evidence. Every event distinguishes its occurrence or observation time from when it was recorded; later tester confirmations are not represented as the reply's exact completion time. The agent uses `qa-publish` to validate and commit its own run directly to this repository's `main`. No browser write API, database or result PR is required. Agents must never turn an unobserved condition into a pass.

The normal run sequence is:

1. Pin the case revision and inspect the actual QA environment.
2. Run a selected variant with timed steps and collect direct observations.
3. Record pass, fail, blocked or not-in-build, with reasons and cleanup.
4. Validate and inspect the public diff, then commit results to `main`.
5. Refresh the viewer after publication.

Only intentionally public, redacted evidence may be committed. Do not store emails, credentials, provider work orders, private logs or chat transcripts. User-requested screenshots may be included as small PNGs without text or EXIF metadata **after visual review**. Run `python3 scripts/sanitize-png.py <private-original.png> runs/<date>/<tester>/<run-id>/evidence/<name>.png` to strip embedded metadata without overwriting the original, then inspect the resulting pixels before commit. The validator cannot detect secrets in pixels. The validator catches common leak patterns in text, but human review remains necessary.
