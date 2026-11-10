# Agent Relay Docker QA template

One ephemeral Docker container per Agent Relay session, for Claude Code or Cursor pools. The relay selects a provider with the fixed `self_hosted_provider` template parameter. The container runs on the Docker daemon local to the provisioner at `unix:///var/run/docker.sock`; this source has no remote Docker hosts, Kata resources, credentials, or persistent volumes.

## Parameters

| Name | Default | Mutable | Purpose |
| --- | --- | --- | --- |
| `container_image` | `ghcr.io/coder/agent-relay-workspace:latest` | No | Image with both provider CLIs. Terraform resolves and uses a registry digest on each build; record the `image_digest` Coder metadata on every test workspace. A moving tag can resolve differently on a later build, so check the digest again after a rebuild. |
| `cpu` | `2` | Yes | CPU cores, from 1 to 16. |
| `memory` | `4` | Yes | Memory in GiB, from 1 to 32. |
| `self_hosted_provider` | `claude` | No | `claude` or `cursor`; the pool sets this in `template_parameters`. |
| `forced_failure_mode` | `none` | Yes | `none`, `terraform_build`, `coder_agent_connection`, or `anthropic_agent_execution`. The last mode replaces the selected provider CLI with `/bin/false`, including for Cursor. |
| `start_build_delay_seconds` | `0` | Yes | QA-only delay before the runner container starts, from 0 to 480 seconds. A replacement start build waits again; stop and delete builds do not wait. Use only for disposable sessions, and verify cancel latency on the provisioner before testing an eight-minute build. |

The selected 1.0.0 runner modules declare their own session parameters. `.terraform.lock.hcl` pins the resolved Coder and Docker provider plugins; run `terraform init -backend=false` after changing provider constraints and commit the updated lock file. Do not duplicate module parameters or place pool credentials in fixed template parameters. Agent Relay requires build-secret transport on Coder 2.39 or newer for these module versions; an older Coder release requires an explicitly opted-in legacy transport and is not a target for this QA template.

The agent publishes `agent_relay_status` every 10 seconds and `agent_relay_session_attached` every 30 seconds from the selected module's scripts. The relay uses the first for reaping and fresh `attached` samples from the second for keepalive. The image must have the selected provider CLI. The default image has both.

## Publishing checklist

The template was first published in `steven` on 2026-11-04 from source commit `73079d4`. Its initial active version ID was `2267ce10-44a7-4cc4-a209-4fd7d088b60f`; `allow_user_cancel_workspace_jobs=true`, `require_active_version=false` and default TTL `16h` were verified. These are a snapshot, not an assertion that the live deployment remains unchanged.

1. For subsequent updates, run `scripts/publish-template.sh` from a clean `main` checkout after verifying the deployment and the `steven-home` provisioner. The script publishes only the `steven` template with the `owner=` and `scope=organization` tags, then reapplies cancellation, active-version and TTL settings. It does not select `steven-home` by key, so another provisioner with the same matching tags could claim jobs.
2. Verify the template version, tags and an actual build before routing live QA traffic. `terraform validate` checks syntax and module wiring but cannot prove the provisioner, Docker daemon, Coder version, image availability or relay pool configuration are correct.
3. Grant the relay service account appropriate access and set each QA pool's `organization` to `steven`, `template` to `agent-relay-qa-docker`, and `template_parameters.self_hosted_provider` to `claude` or `cursor` respectively. Do not store provider secrets in this public repository.

`terraform_build` intentionally reports an error after creating the container. `coder_agent_connection` uses an invalid agent token. `anthropic_agent_execution` replaces the CLI with `/bin/false`. These failure controls should be used only for disposable QA sessions.
