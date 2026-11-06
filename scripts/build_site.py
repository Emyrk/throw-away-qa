#!/usr/bin/env python3
"""Generate concise public results from the report and validated run evidence."""

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


def concise_results(report, cases, runs):
    variants = {variant["id"]: variant for case in cases for variant in case["variants"]}
    latest = {}
    for run in runs:
        for result in run["results"]:
            variant_id = result["variant_id"]
            previous = latest.get(variant_id)
            observed = datetime.fromisoformat(result["observed_at"].replace("Z", "+00:00"))
            previous_observed = (
                datetime.fromisoformat(previous["result"]["observed_at"].replace("Z", "+00:00"))
                if previous else None
            )
            if previous_observed is None or observed > previous_observed:
                latest[variant_id] = {"result": result, "run": run}

    summaries = {}
    for line in report.splitlines():
        if not line.startswith("| Q"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 4 or any(not cell for cell in cells) or cells[0] in summaries:
            raise ValueError(f"invalid or repeated result summary: {line}")
        summaries[cells[0]] = dict(zip(("variant_id", "tried", "happened", "wanted"), cells))

    if summaries.keys() - latest.keys():
        raise ValueError(f"report contains unrecorded results: {sorted(summaries.keys() - latest.keys())}")

    output = []
    for variant_id, entry in latest.items():
        result, run = entry["result"], entry["run"]
        summary = summaries.get(variant_id)
        if summary is None:
            variant = variants[variant_id]
            summary = {
                "variant_id": variant_id,
                "tried": variant["title"] + ".",
                "happened": f"A {result['status']} result was recorded; summary pending.",
                "wanted": variant["summary"].split(". ", 1)[0].rstrip(".") + ".",
            }
        images = [str(Path(run["path"]) / path) for path in result["evidence"] if path.lower().endswith(".png")]
        output.append({**summary, "status": result["status"], "images": images})
    return output


def main():
    cases, runs = collect()
    report = (ROOT / "RESULTS.md").read_text(encoding="utf-8")
    results = concise_results(report, cases, runs)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source_revision": revision(),
        "run_count": len(runs),
        "results": results,
    }
    output = ROOT / "web" / "data.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"built {output.relative_to(ROOT)}: {len(results)} latest results, {len(runs)} runs")


if __name__ == "__main__":
    main()
