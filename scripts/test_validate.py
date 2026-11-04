#!/usr/bin/env python3
"""Regression tests for case and result validation."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import validate


CASE = {
    "id": "Q01", "title": "Smoke", "summary": "Confirms a healthy QA runner can answer a test request.", "providers": ["cursor"], "priority": "P0",
    "prs": [96], "estimated_minutes": 15, "prerequisites": [], "config": {}, "notes": [],
    "variants": [{"id": "Q01-a", "title": "Run", "summary": "Checks that a workspace becomes ready within the expected window.", "cleanup": ["Delete QA workspace"], "steps": [
        {"action": "Start", "wait_seconds": 0, "poll_seconds": 10, "timeout_seconds": 60,
         "expected": "Ready", "evidence": "Record status"}
    ]}],
}


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "cases").mkdir()
        (self.root / "runs" / "2026-11-04" / "tester" / "run-123").mkdir(parents=True)
        self.run = self.root / "runs" / "2026-11-04" / "tester" / "run-123"
        self.write(self.root / "cases" / "Q01.json", CASE)
        self.write(self.run / "manifest.json", {
            "run_id": "run-123", "tester": "tester", "started_at": "2026-11-04T18:00:00Z",
            "suite_revision": "abc", "relay_revision": "def", "organization": "steven",
        })
        self.write(self.run / "Q01-a.json", {
            "case_id": "Q01", "variant_id": "Q01-a", "status": "pass",
            "observed_at": "2026-11-04T18:05:00Z", "observations": ["Saw ready at 18:05Z"],
            "evidence": [], "cleanup": "No resources created",
        })
        self.patches = [
            patch.object(validate, "CASES", self.root / "cases"),
            patch.object(validate, "RUNS", self.root / "runs"),
            patch.object(validate, "ROOT", self.root),
        ]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_valid_run(self):
        cases, runs = validate.collect()
        self.assertEqual("Q01", cases[0]["id"])
        self.assertEqual("pass", runs[0]["results"][0]["status"])

    def test_missing_summary_rejected(self):
        path = self.root / "cases" / "Q01.json"
        case = json.loads(path.read_text())
        del case["summary"]
        self.write(path, case)
        with self.assertRaisesRegex(validate.Invalid, "summary must be a short"):
            validate.collect()

    def test_variant_summary_rejected_when_over_two_sentences(self):
        path = self.root / "cases" / "Q01.json"
        case = json.loads(path.read_text())
        case["variants"][0]["summary"] = "One test. Another test. A third test."
        self.write(path, case)
        with self.assertRaisesRegex(validate.Invalid, "one or two complete sentences"):
            validate.collect()

    def test_unobserved_result_rejected(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["observations"] = []
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "observations required"):
            validate.collect()

    def test_nonpass_requires_reason(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["status"] = "blocked"
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "needs a reason"):
            validate.collect()

    def test_email_leak_rejected(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["observations"] = ["Owner " + "person" + "@" + "example.com"]
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "possible secret or email"):
            validate.collect()

    def test_binary_evidence_rejected(self):
        (self.run / "snapshot.png").write_bytes(b"not reviewed")
        with self.assertRaisesRegex(validate.Invalid, "unsupported evidence type"):
            validate.collect()

    def test_path_escape_rejected(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["evidence"] = ["../../../../cases/Q01.json"]
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "escapes run"):
            validate.collect()


if __name__ == "__main__":
    unittest.main()
