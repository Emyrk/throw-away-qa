#!/usr/bin/env python3
"""Render a private, nonsecret local relay config from the public QA baseline."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "config" / "baseline.json"
DESTINATION = Path.home() / ".config" / "agent-relay-qa" / "config.yaml"


def render():
    baseline = json.loads(SOURCE.read_text(encoding="utf-8"))
    if baseline.get("status") != "QA_LOCAL_CONFIG":
        raise ValueError("unexpected baseline status; review config before rendering")
    config = baseline["config"].copy()
    if config.get("coderdURL") != "https://dogfood.cdr.dev" or config.get("statusUIAuth") != "coder-token":
        raise ValueError("unexpected deployment or status authentication in baseline")
    if config.get("dangerousAllowParameterCredentialTransport"):
        raise ValueError("legacy credential parameter transport is forbidden in QA")
    for name in ("claudeCodeRunnerPools", "cursorWorkerPools"):
        for pool in config.get(name, []):
            if pool.get("organization") != "steven" or pool.get("template") != "agent-relay-qa-docker":
                raise ValueError(f"{name}: pool must target the steven QA template")
            if not pool.get("secret_env") or "secret" in pool:
                raise ValueError(f"{name}: only secret_env is allowed")
    if config.get("prometheusAddress") != "127.0.0.1:22112" or config.get("statusUIAddress") != "127.0.0.1:22113":
        raise ValueError("QA listeners must use this workspace's loopback ports")
    return json.dumps(config, indent=2) + "\n"


def main():
    payload = render()
    DESTINATION.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if DESTINATION.exists() or DESTINATION.is_symlink():
        raise SystemExit(f"Refusing to overwrite {DESTINATION}; preserve local QA overlays")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(DESTINATION, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as output:
        output.write(payload)
    print(f"Wrote nonsecret config to {DESTINATION}. Review pool names before starting.")


if __name__ == "__main__":
    main()
