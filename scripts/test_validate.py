#!/usr/bin/env python3
"""Regression tests for case and result validation."""

import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

import validate


CASE = {
    "id": "Q01", "title": "Smoke", "summary": "Confirms a healthy QA runner can answer a test request.", "providers": ["cursor"], "priority": "P0",
    "prs": [96], "estimated_minutes": 15, "prerequisites": [], "config": {}, "notes": [],
    "variants": [{"id": "Q01-a", "title": "Run", "summary": "Checks that a workspace becomes ready within the expected window.", "cleanup": ["Delete QA workspace"], "steps": [
        {"action": "Start", "wait_seconds": 0, "poll_seconds": 10, "timeout_seconds": 60,
         "expected": "Ready", "evidence": "Record status"},
        {"action": "Confirm reply", "wait_seconds": 0, "poll_seconds": 0, "timeout_seconds": 60,
         "expected": "Reply", "evidence": "Record tester confirmation"}
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
            "events": [{
                "at": "2026-11-04T18:00:00Z", "recorded_at": "2026-11-04T18:00:00Z",
                "source": "operator", "kind": "run_started", "time_basis": "event",
                "summary": "The QA run began."
            }],
        })
        self.write(self.run / "Q01-a.json", {
            "case_id": "Q01", "variant_id": "Q01-a", "status": "pass",
            "observed_at": "2026-11-04T18:05:00Z", "observations": ["Saw ready and reply at 18:05Z"],
            "events": [
                {"at": "2026-11-04T18:01:00.123456789Z", "recorded_at": "2026-11-04T18:02:00Z",
                 "source": "relay_log", "kind": "workspace_ready", "time_basis": "event", "step": 1,
                 "subject": "claude-a", "summary": "The QA workspace was ready."},
                {"at": "2026-11-04T18:05:00Z", "recorded_at": "2026-11-04T18:05:00Z",
                 "source": "tester", "kind": "reply_confirmed", "time_basis": "confirmation", "step": 2,
                 "subject": "claude-a", "summary": "The tester confirmed a reply."}
            ],
            "evidence": [], "cleanup": "The QA workspace was cleaned up",
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

    @staticmethod
    def png_chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    def png_image(self, extra=b""):
        header = self.png_chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        pixels = self.png_chunk(b"IDAT", zlib.compress(b"\x00\xff\x00\x00\xff"))
        return validate.PNG_SIGNATURE + header + extra + pixels + self.png_chunk(b"IEND", b"")

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

    def test_manifest_without_timeline_rejected(self):
        path = self.run / "manifest.json"
        manifest = json.loads(path.read_text())
        del manifest["events"]
        self.write(path, manifest)
        with self.assertRaisesRegex(validate.Invalid, "timestamped event is required"):
            validate.collect()

    def test_result_without_timeline_rejected(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        del result["events"]
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "timestamped event is required"):
            validate.collect()

    def test_event_raw_payload_field_rejected(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["events"][0]["raw_response"] = "unreviewed payload"
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "unexpected field"):
            validate.collect()

    def test_missing_recorded_at_rejected(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        del result["events"][0]["recorded_at"]
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "recorded_at"):
            validate.collect()

    def test_bad_timestamp_rejected(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["events"][0]["at"] = "2026-11-04T18:01:00+01:00"
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "UTC RFC3339"):
            validate.collect()

    def test_events_must_be_chronological(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["events"].reverse()
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "ordered by event time"):
            validate.collect()

    def test_nanosecond_event_order_preserved(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["events"][1]["at"] = "2026-11-04T18:01:00.123456788Z"
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "ordered by event time"):
            validate.collect()

    def test_pass_requires_each_step_timestamped(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["events"] = result["events"][:1]
        self.write(path, result)
        with self.assertRaisesRegex(validate.Invalid, "every step"):
            validate.collect()

    def test_blocked_requires_event_but_not_every_step(self):
        path = self.run / "Q01-a.json"
        result = json.loads(path.read_text())
        result["status"] = "blocked"
        result["reason"] = "QA account was not enabled"
        result["events"] = result["events"][:1]
        self.write(path, result)
        _, runs = validate.collect()
        self.assertEqual("blocked", runs[0]["results"][0]["status"])

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

    def test_invalid_png_rejected(self):
        (self.run / "snapshot.png").write_bytes(b"not a screenshot")
        with self.assertRaisesRegex(validate.Invalid, "invalid PNG signature"):
            validate.collect()

    def test_redacted_png_accepted(self):
        (self.run / "snapshot.png").write_bytes(self.png_image())
        _, runs = validate.collect()
        self.assertEqual("pass", runs[0]["results"][0]["status"])

    def test_png_metadata_chunk_rejected(self):
        metadata = self.png_chunk(b"tEXt", b"private=unreviewed")
        (self.run / "snapshot.png").write_bytes(self.png_image(extra=metadata))
        with self.assertRaisesRegex(validate.Invalid, "unsupported PNG metadata"):
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
