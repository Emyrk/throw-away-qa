#!/bin/sh
# Publish only the QA Docker template and its required Coder metadata.
set -eu

repo=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
cd "$repo"

case "${CODER_URL:-}" in
  https://dogfood.cdr.dev|https://dogfood.cdr.dev/) ;;
  *) echo 'Set CODER_URL to https://dogfood.cdr.dev before publishing.' >&2; exit 1 ;;
esac
if [ "$(git branch --show-current)" != main ] || [ "$(git config --get remote.origin.url)" != 'https://github.com/Emyrk/throw-away-qa.git' ]; then
  echo 'Publish only from Emyrk/throw-away-qa main.' >&2
  exit 1
fi
if [ -n "$(git status --porcelain)" ]; then
  echo 'Commit and validate template changes before publishing.' >&2
  exit 1
fi
remote_head=$(git ls-remote origin refs/heads/main | awk '{print $1}')
if [ -z "$remote_head" ] || [ "$remote_head" != "$(git rev-parse HEAD)" ]; then
  echo 'Publish only after local main matches the pushed QA main revision.' >&2
  exit 1
fi

terraform -chdir=templates/agent-relay-docker fmt -check
terraform -chdir=templates/agent-relay-docker init -backend=false -input=false
terraform -chdir=templates/agent-relay-docker validate

coder templates push --org steven \
  --directory templates/agent-relay-docker \
  --provisioner-tag 'owner=' --provisioner-tag 'scope=organization' \
  --message "QA source $(git rev-parse --short HEAD)" \
  --yes agent-relay-qa-docker

coder templates edit --org steven \
  --allow-user-cancel-workspace-jobs=true \
  --default-ttl=16h \
  --require-active-version=false \
  --yes agent-relay-qa-docker

echo 'Published QA template. Verify organization, version, tags, and live build before routing sessions.'
