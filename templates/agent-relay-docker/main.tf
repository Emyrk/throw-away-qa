terraform {
  required_version = ">= 1.5.0"

  required_providers {
    coder = {
      source  = "coder/coder"
      version = ">= 2.13.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 4.0"
    }
  }
}

provider "coder" {}
provider "docker" {
  host = "unix:///var/run/docker.sock"
}

data "coder_workspace" "me" {}
data "coder_workspace_owner" "me" {}

locals {
  workspace_owner_slug  = replace(lower(data.coder_workspace_owner.me.name), "/[^a-z0-9-]/", "-")
  workspace_name_slug   = replace(lower(data.coder_workspace.me.name), "/[^a-z0-9-]/", "-")
  container_name_prefix = trimsuffix(substr("coder-${local.workspace_owner_slug}-${local.workspace_name_slug}", 0, 54), "-")
  container_name        = "${local.container_name_prefix}-${substr(data.coder_workspace.me.id, 0, 8)}"
  cpu_limit             = tonumber(data.coder_parameter.cpu.value)
  memory_limit_mb       = tonumber(data.coder_parameter.memory.value) * 1024
  forced_failure_mode   = data.coder_parameter.forced_failure_mode.value
  coder_agent_token     = local.forced_failure_mode == "coder_agent_connection" ? "intentionally-invalid-agent-token" : coder_agent.main.token
  self_hosted_provider  = data.coder_parameter.self_hosted_provider.value
  runner_binary         = local.forced_failure_mode == "anthropic_agent_execution" ? "/bin/false" : (local.self_hosted_provider == "cursor" ? "agent" : "claude")

  # Only the selected module's parameters exist on a build. Indexed output
  # references avoid a dependency cycle between the module and the agent.
  status_metadata_script           = try(module.cursor_worker[0].status_metadata_script, module.claude_code_runner[0].status_metadata_script)
  session_attached_metadata_script = try(module.cursor_worker[0].session_attached_metadata_script, module.claude_code_runner[0].session_attached_metadata_script)
}

data "coder_parameter" "container_image" {
  name         = "container_image"
  display_name = "Container image"
  description  = "Workspace image containing the Claude Code and Cursor CLIs."
  type         = "string"
  default      = "ghcr.io/coder/agent-relay-workspace:latest"
  mutable      = false
  order        = 1
}

data "coder_parameter" "cpu" {
  name         = "cpu"
  display_name = "CPU cores"
  type         = "number"
  default      = "2"
  mutable      = true
  order        = 2

  validation {
    min = 1
    max = 16
  }
}

data "coder_parameter" "memory" {
  name         = "memory"
  display_name = "Memory in GiB"
  type         = "number"
  default      = "4"
  mutable      = true
  order        = 3

  validation {
    min = 1
    max = 32
  }
}

data "coder_parameter" "self_hosted_provider" {
  name         = "self_hosted_provider"
  display_name = "Self-hosted provider"
  description  = "Agent Relay pools set this through template_parameters."
  type         = "string"
  default      = "claude"
  mutable      = false
  order        = 4

  option {
    name  = "Claude Code"
    value = "claude"
    icon  = "/icon/claude.svg"
  }
  option {
    name  = "Cursor"
    value = "cursor"
    icon  = "/icon/cursor.svg"
  }
}

data "coder_parameter" "forced_failure_mode" {
  name         = "forced_failure_mode"
  display_name = "Forced failure mode"
  description  = "Intentionally break one startup stage for failure-path QA."
  type         = "string"
  default      = "none"
  mutable      = true
  order        = 5

  option {
    name  = "None"
    value = "none"
  }
  option {
    name  = "Fail to build in Terraform"
    value = "terraform_build"
  }
  option {
    name  = "Coder agent fail to connect"
    value = "coder_agent_connection"
  }
  option {
    name  = "Fail to execute Anthropic agent"
    value = "anthropic_agent_execution"
  }
}

data "coder_parameter" "start_build_delay_seconds" {
  name         = "start_build_delay_seconds"
  display_name = "Start build delay in seconds"
  description  = "Hold QA start builds pending before the runner container exists."
  type         = "number"
  default      = "0"
  mutable      = true
  order        = 6

  validation {
    min = 0
    max = 480
  }
}

resource "coder_agent" "main" {
  arch                    = "amd64"
  os                      = "linux"
  startup_script_behavior = "non-blocking"

  # The runner module owns the provider's credential environment.
  env = {
    CODER_WORKSPACE_ID = data.coder_workspace.me.id
  }

  metadata {
    key          = "agent_relay_status"
    display_name = "Session"
    script       = local.status_metadata_script
    interval     = 10
    timeout      = 5
  }

  metadata {
    key          = "agent_relay_session_attached"
    display_name = "Session attached"
    script       = local.session_attached_metadata_script
    interval     = 30
    timeout      = 5
  }
}

module "claude_code_runner" {
  count      = local.self_hosted_provider == "claude" ? 1 : 0
  source     = "registry.coder.com/coder/agent-relay-claude-code/coder"
  version    = "1.0.0"
  agent_id   = coder_agent.main.id
  cli_binary = local.runner_binary
}

module "cursor_worker" {
  count      = local.self_hosted_provider == "cursor" ? 1 : 0
  source     = "registry.coder.com/coder/agent-relay-cursor/coder"
  version    = "1.0.0"
  agent_id   = coder_agent.main.id
  cli_binary = local.runner_binary
}

module "git-config" {
  count                 = data.coder_workspace.me.start_count
  source                = "registry.coder.com/coder/git-config/coder"
  version               = "1.0.34"
  agent_id              = coder_agent.main.id
  allow_username_change = false
  allow_email_change    = false
}

data "docker_registry_image" "workspace" {
  name = data.coder_parameter.container_image.value
}

resource "docker_image" "workspace" {
  name = "${data.coder_parameter.container_image.value}@${data.docker_registry_image.workspace.sha256_digest}"
  pull_triggers = [
    data.docker_registry_image.workspace.sha256_digest,
  ]
  keep_locally = true
}

resource "terraform_data" "start_build_delay" {
  count = data.coder_workspace.me.start_count * (tonumber(data.coder_parameter.start_build_delay_seconds.value) > 0 ? 1 : 0)

  # Each replacement start build must wait, even if an earlier apply left state.
  triggers_replace = plantimestamp()

  provisioner "local-exec" {
    command = "echo 'QA start build delay started' >&2; exec sleep \"$DELAY_SECONDS\""
    environment = {
      DELAY_SECONDS = data.coder_parameter.start_build_delay_seconds.value
    }
  }
}

resource "docker_container" "workspace" {
  count = data.coder_workspace.me.start_count

  depends_on = [terraform_data.start_build_delay]

  image    = docker_image.workspace.image_id
  name     = local.container_name
  hostname = data.coder_workspace.me.name

  entrypoint = ["sh", "-c", coder_agent.main.init_script]
  env = [
    "CODER_AGENT_TOKEN=${local.coder_agent_token}",
  ]

  memory = local.memory_limit_mb
  cpus   = local.cpu_limit

  # Sessions are ephemeral and have no persistent volumes.
  restart               = "unless-stopped"
  stop_signal           = "SIGINT"
  stop_timeout          = 30
  destroy_grace_seconds = 30

  host {
    host = "host.docker.internal"
    ip   = "host-gateway"
  }

  labels {
    label = "coder.owner"
    value = data.coder_workspace_owner.me.name
  }
  labels {
    label = "coder.owner_id"
    value = data.coder_workspace_owner.me.id
  }
  labels {
    label = "coder.workspace_id"
    value = data.coder_workspace.me.id
  }
  labels {
    label = "coder.workspace_name"
    value = data.coder_workspace.me.name
  }
}

# Create the container before reporting a forced Terraform build failure.
resource "terraform_data" "forced_build_failure" {
  count = data.coder_workspace.me.start_count * (local.forced_failure_mode == "terraform_build" ? 1 : 0)

  depends_on = [
    docker_container.workspace,
  ]

  provisioner "local-exec" {
    command = <<-EOT
      echo "Forced failure mode: Terraform build failure after starting the workspace container" >&2
      exit 1
    EOT
  }
}

resource "coder_metadata" "container" {
  count       = data.coder_workspace.me.start_count
  resource_id = docker_container.workspace[0].id

  item {
    key   = "image"
    value = data.coder_parameter.container_image.value
  }
  item {
    key   = "image_digest"
    value = data.docker_registry_image.workspace.sha256_digest
  }
  item {
    key   = "memory"
    value = "${data.coder_parameter.memory.value} GiB"
  }
  item {
    key   = "cpu"
    value = "${data.coder_parameter.cpu.value} cores"
  }
}
