#!/bin/sh
# Start only the dedicated QA relay in this Coder workspace.
set -eu
umask 077

binary="${HOME}/.local/bin/agent-relay-qa"
config="${HOME}/.config/agent-relay-qa/config.yaml"
secrets_file="${HOME}/.config/agent-relay-qa/secrets.env"

if [ "${AGENT_RELAY_QA_POOLS_CONFIRMED:-}" != yes ]; then
  echo 'Confirm both provider-side pools are QA-only, then set AGENT_RELAY_QA_POOLS_CONFIRMED=yes.' >&2
  exit 1
fi
if [ ! -x "$binary" ] || [ ! -r "$config" ]; then
  echo 'Build the pinned QA binary and render the local config first.' >&2
  exit 1
fi

if [ -e "$secrets_file" ] || [ -L "$secrets_file" ]; then
  if [ -L "$secrets_file" ] || [ ! -f "$secrets_file" ] || [ "$(stat -c %a "$secrets_file")" != 600 ] || [ "$(stat -c %u "$secrets_file")" != "$(id -u)" ]; then
    echo 'QA secrets file must be owned by this user, regular, and mode 0600.' >&2
    exit 1
  fi
  # This file is owned by the operator and may contain shell assignments.
  set -a
  # shellcheck source=/dev/null
  . "$secrets_file"
  set +a
fi

if [ -z "${CODER_AGENT_RELAY_CODERD_SESSION_TOKEN:-}" ] ||
   [ -z "${QA_CLAUDE_POOL_SECRET:-}" ] ||
   [ -z "${QA_CURSOR_SERVICE_ACCOUNT_KEY:-}" ]; then
  echo 'Missing a QA-only service account token or provider credential environment variable.' >&2
  exit 1
fi
if [ "${CODER_AGENT_RELAY_CODERD_SESSION_TOKEN}" = "${CODER_SESSION_TOKEN:-}" ]; then
  echo 'Use a dedicated service-account token, not this workspace user session token.' >&2
  exit 1
fi
if [ "${CODER_AGENT_RELAY_DANGEROUS_ALLOW_PARAMETER_CREDENTIAL_TRANSPORT:-false}" != false ]; then
  echo 'Legacy parameter credential transport is not allowed in this QA workspace.' >&2
  exit 1
fi

# Logs may include provider errors. Keep them private and never commit them.
exec "$binary" start --config "$config" >> "${HOME}/.config/agent-relay-qa/relay.log" 2>&1
