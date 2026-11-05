#!/usr/bin/env python3
"""Validate public QA case definitions and committed run evidence."""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "cases"
RUNS = ROOT / "runs"
STATUSES = {"pass", "fail", "blocked", "not-in-build"}
EVENT_SOURCES = {"relay_log", "coder_api", "metrics", "tester", "operator", "provider_ui", "provider_api", "script"}
TIME_BASES = {"event", "observation", "confirmation"}
UTC_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,9})?Z$")
SECRET = re.compile(
    r"(?:[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}|"
    r"(?:gh[pousr]_|github_pat_|sk-ant-|sk-proj-)[A-Za-z0-9_-]{8,}|"
    r"eyJ[A-Za-z0-9_-]{16,}\.eyJ[A-Za-z0-9_-]{16,}|"
    r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|"
    r"(?i:Bearer\s+[A-Za-z0-9._-]{12,})|"
    r"(?i:(?:CODER_SESSION_TOKEN|CODER_AGENT_RELAY_CODERD_SESSION_TOKEN)\s*[:=]\s*\S+))"
)


class Invalid(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Invalid(message)


def load_json(path):
    require(not path.is_symlink(), f"symlink not allowed: {path}")
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text), text
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Invalid(f"{path}: {exc}") from exc


def check_public(path, text):
    require(not SECRET.search(text), f"possible secret or email in {path}; redact before committing")


def validate_summary(value, path):
    require(isinstance(value, str) and 20 <= len(value.strip()) <= 320, f"{path}: summary must be a short, nonempty string")
    sentences = re.split(r"(?<=[.!?])\s+", value.strip())
    require(1 <= len(sentences) <= 2 and all(sentence.endswith((".", "!", "?")) for sentence in sentences),
            f"{path}: summary must be one or two complete sentences")


def validate_timestamp(value, path):
    require(isinstance(value, str) and UTC_TIMESTAMP.fullmatch(value), f"{path}: expected a UTC RFC3339 timestamp ending in Z")
    try:
        second = datetime.fromisoformat(value[:19] + "+00:00")
        fraction = value[19:-1]
        nanoseconds = int(fraction[1:].ljust(9, "0")) if fraction else 0
        return second, nanoseconds
    except ValueError as exc:
        raise Invalid(f"{path}: invalid calendar timestamp") from exc


def validate_events(events, path, step_count=None):
    require(isinstance(events, list) and events, f"{path}: at least one timestamped event is required")
    previous = None
    first = None
    covered_steps = set()
    for index, event in enumerate(events, start=1):
        location = f"{path}: event {index}"
        require(isinstance(event, dict), f"{location}: expected object")
        require(set(event).issubset({"at", "recorded_at", "source", "kind", "time_basis", "summary", "subject", "step"}),
                f"{location}: unexpected field; store only public-safe timeline fields")
        at = validate_timestamp(event.get("at"), f"{location} at")
        validate_timestamp(event.get("recorded_at"), f"{location} recorded_at")
        require(previous is None or previous <= at, f"{location}: events must be ordered by event time")
        if first is None:
            first = at
        previous = at
        require(event.get("source") in EVENT_SOURCES, f"{location}: invalid source")
        require(event.get("time_basis") in TIME_BASES, f"{location}: invalid time_basis")
        kind = event.get("kind")
        require(isinstance(kind, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,63}", kind), f"{location}: invalid kind")
        summary = event.get("summary")
        require(isinstance(summary, str) and 8 <= len(summary.strip()) <= 500 and "\n" not in summary,
                f"{location}: summary must be a short, single-line observation")
        subject = event.get("subject")
        if subject is not None:
            require(isinstance(subject, str) and re.fullmatch(r"[a-z][a-z0-9_-]{0,39}", subject)
                    and not re.search(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", subject),
                    f"{location}: subject must be a short pseudonym, not a raw ID")
        step = event.get("step")
        if step is not None:
            require(step_count is not None and type(step) is int and 1 <= step <= step_count,
                    f"{location}: step must name a step of this variant")
            covered_steps.add(step)
    return covered_steps, first, previous


def validate_case(path):
    case, text = load_json(path)
    check_public(path, text)
    require(isinstance(case, dict), f"{path}: expected object")
    require(case.get("id") == path.stem and re.fullmatch(r"Q\d{2}", path.stem), f"{path}: case ID must match filename")
    for field in ("title", "priority"):
        require(isinstance(case.get(field), str) and case[field], f"{path}: missing {field}")
    validate_summary(case.get("summary"), f"{path}: case")
    require(case["priority"] in {"P0", "P1", "P2"}, f"{path}: invalid priority")
    for field in ("providers", "prs", "prerequisites", "notes"):
        require(isinstance(case.get(field), list), f"{path}: {field} must be a list")
    require(all(isinstance(n, int) and n > 0 for n in case["prs"]), f"{path}: invalid PR number")
    require(isinstance(case.get("estimated_minutes"), int) and case["estimated_minutes"] > 0, f"{path}: invalid duration")
    require(isinstance(case.get("config"), dict), f"{path}: config must be an object")
    variants = case.get("variants")
    require(isinstance(variants, list) and variants, f"{path}: at least one variant is required")
    seen = set()
    for variant in variants:
        require(isinstance(variant, dict), f"{path}: invalid variant")
        vid = variant.get("id")
        require(isinstance(vid, str) and vid.startswith(path.stem + "-") and vid not in seen, f"{path}: invalid or repeated variant ID")
        seen.add(vid)
        require(isinstance(variant.get("title"), str) and variant["title"], f"{path}: missing variant title")
        validate_summary(variant.get("summary"), f"{path}: {vid}")
        require(isinstance(variant.get("cleanup"), list), f"{path}: variant cleanup must be a list")
        steps = variant.get("steps")
        require(isinstance(steps, list) and steps, f"{path}: variant must have steps")
        for step in steps:
            require(isinstance(step, dict), f"{path}: invalid step")
            for field in ("action", "expected", "evidence"):
                require(isinstance(step.get(field), str) and step[field], f"{path}: step missing {field}")
            for field in ("wait_seconds", "poll_seconds", "timeout_seconds"):
                require(type(step.get(field)) is int and step[field] >= 0, f"{path}: step has invalid {field}")
    return case


def validate_run(run_dir, cases):
    require(not run_dir.is_symlink(), f"symlink not allowed: {run_dir}")
    manifest_path = run_dir / "manifest.json"
    require(manifest_path.is_file(), f"{run_dir}: missing manifest.json")
    manifest, text = load_json(manifest_path)
    check_public(manifest_path, text)
    require(isinstance(manifest, dict), f"{manifest_path}: expected object")
    for field in ("run_id", "tester", "started_at", "suite_revision", "relay_revision", "organization"):
        require(isinstance(manifest.get(field), str) and manifest[field], f"{manifest_path}: missing {field}")
    require(manifest["organization"] == "steven", f"{manifest_path}: wrong organization")
    require(manifest["run_id"] == run_dir.name, f"{manifest_path}: run_id must match directory")
    start = validate_timestamp(manifest["started_at"], f"{manifest_path}: started_at")
    end = validate_timestamp(manifest["ended_at"], f"{manifest_path}: ended_at") if "ended_at" in manifest else None
    require(end is None or start <= end, f"{manifest_path}: ended_at precedes started_at")
    _, first, last = validate_events(manifest.get("events"), str(manifest_path))
    require(start <= first and (end is None or last <= end), f"{manifest_path}: event outside run window")
    results = []
    for path in sorted(run_dir.glob("Q*.json")):
        result, text = load_json(path)
        check_public(path, text)
        require(isinstance(result, dict), f"{path}: result must be an object")
        case = cases.get(result.get("case_id"))
        require(case is not None, f"{path}: unknown case")
        variant_id = result.get("variant_id")
        require(variant_id == path.stem and any(v["id"] == variant_id for v in case["variants"]), f"{path}: variant_id must match filename and case")
        require(result.get("status") in STATUSES, f"{path}: invalid final status")
        require(isinstance(result.get("observed_at"), str) and result["observed_at"], f"{path}: missing observation time")
        observed_at = validate_timestamp(result["observed_at"], f"{path}: observed_at")
        require(isinstance(result.get("observations"), list) and result["observations"], f"{path}: observations required")
        variant = next(v for v in case["variants"] if v["id"] == variant_id)
        covered_steps, _, last = validate_events(result.get("events"), str(path), len(variant["steps"]))
        require(last <= observed_at, f"{path}: event after observed_at")
        if result["status"] == "pass":
            require(covered_steps == set(range(1, len(variant["steps"]) + 1)), f"{path}: passing result needs timestamped evidence for every step")
        require(isinstance(result.get("cleanup"), str) and result["cleanup"], f"{path}: cleanup disposition required")
        require(isinstance(result.get("evidence"), list), f"{path}: evidence must be a list")
        if result["status"] != "pass":
            require(isinstance(result.get("reason"), str) and result["reason"], f"{path}: non-pass needs a reason")
        for item in result["evidence"]:
            require(isinstance(item, str) and item and not Path(item).is_absolute(), f"{path}: invalid evidence path")
            resolved = (run_dir / item).resolve()
            require(resolved.is_relative_to(run_dir.resolve()) and resolved.is_file(), f"{path}: evidence missing or escapes run")
        results.append(result)
    for path in run_dir.rglob("*"):
        require(not path.is_symlink(), f"symlink not allowed: {path}")
        if path.is_file():
            require(path.suffix.lower() in {".txt", ".json", ".md", ".log", ".csv"}, f"{path}: unsupported evidence type; only reviewable text is allowed")
            check_public(path, path.read_text(encoding="utf-8"))
    return {"path": str(run_dir.relative_to(ROOT)), "manifest": manifest, "results": results}


def collect():
    require(CASES.is_dir(), "missing cases/ directory")
    cases = {case["id"]: case for case in (validate_case(path) for path in sorted(CASES.glob("Q*.json")))}
    require(cases, "no cases found")
    runs = []
    if RUNS.exists():
        for path in sorted(RUNS.glob("*/*/*")):
            if path.is_dir():
                runs.append(validate_run(path, cases))
    return list(cases.values()), runs


if __name__ == "__main__":
    try:
        cases, runs = collect()
    except (Invalid, OSError, UnicodeError) as exc:
        print(f"validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"validated {len(cases)} cases and {len(runs)} runs")
