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

The selected 1.0.0 runner module declares its own session parameters. Do not duplicate them in this source or place pool credentials in fixed template parameters. Agent Relay requires build-secret transport on Coder 2.39 or newer for these module versions; an older Coder release requires an explicitly opted-in legacy transport and is not a target for this QA template.

The agent publishes `agent_relay_status` every 10 seconds and `agent_relay_session_attached` every 30 seconds from the selected module's scripts. The relay uses the first for reaping and fresh `attached` samples from the second for keepalive. The image must have the selected provider CLI. The default image has both.

## Publishing checklist (not performed here)

1. Use the intended Coder deployment and organization `steven`. Confirm that the already-running provisioner with key `steven-home` has access to the local Docker socket and is the provisioner expected to claim these jobs. The template source cannot select a provisioner by its key: job matching uses provisioner tags. If other provisioners share the same matching tags, they may also claim jobs.
2. Publish only this directory as the template source. For example, from the repository root, after checking the target deployment and available provisioners:

   ```sh
   coder templates push --org steven --directory templates/agent-relay-docker \
     --provisioner-tag 'owner=' --provisioner-tag 'scope=organization' \
     agent-relay-docker-qa
   ```

   The two tags select organization-scoped provisioner jobs, not a remote Docker endpoint. On an existing template, explicitly passing both avoids inheriting different tags from its active version. Choose the final template name with the operator before publishing.
3. Enable `allow_user_cancel_workspace_jobs` on the template. This is a Coder template setting, not a Terraform setting. Verify it before configuring Agent Relay pools; the relay checks it. Confirm access for the relay service account and set each pool's `organization` to `steven`, `template` to the published name, and `template_parameters.self_hosted_provider` to `claude` or `cursor` respectively. Do not store provider secrets in this public repository.
4. Verify the template's provisioner tags and an actual build in the deployment before routing live QA traffic. `terraform validate` checks syntax and module wiring but cannot prove the provisioner, Docker daemon, Coder version, image availability, or relay pool configuration are correct.

`terraform_build` intentionally reports an error after creating the container. `coder_agent_connection` uses an invalid agent token. `anthropic_agent_execution` replaces the CLI with `/bin/false`. These failure controls should be used only for disposable QA sessions.
