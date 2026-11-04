#!/usr/bin/env python3
"""Generate the static viewer's read-only index from cases and committed runs."""

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from validate import ROOT, collect


def revision():
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def main():
    cases, runs = collect()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_revision": revision(),
        "cases": cases,
        "runs": runs,
    }
    output = ROOT / "web" / "data.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"built {output.relative_to(ROOT)}: {len(cases)} cases, {len(runs)} runs")


if __name__ == "__main__":
    main()
