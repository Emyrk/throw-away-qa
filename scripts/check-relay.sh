#!/bin/sh
# Probe the workspace-local QA relay. Do not commit raw output without review.
set -eu

printf 'Probe started at %s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
printf '%s\n' 'Readiness (200 means at least one pool verified, not both):'
curl --silent --show-error --max-time 5 --write-out '\nHTTP %{http_code}\n' \
  http://127.0.0.1:22112/readyz
printf '\n%s\n' 'Per-pool health and dispatch/reaper counts:'
curl --fail --silent --show-error --max-time 5 \
  http://127.0.0.1:22112/metrics |
  grep -E '^agent_relay_(pool_healthy|dispatcher_dispatches_total|reaper_verdicts_total)' || true
printf '\n%s\n' 'Status UI liveness (the full page requires a reader login):'
curl --silent --show-error --max-time 5 --write-out 'HTTP %{http_code}\n' \
  --output /dev/null http://127.0.0.1:22113/healthz
