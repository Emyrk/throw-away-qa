#!/usr/bin/env python3
"""Tests for the concise results index."""

import unittest

from build_site import concise_results


REPORT = """| Test | Tried | Happened | Wanted |
| --- | --- | --- | --- |
| Q06-c | Sent a follow-up. | Claude replied. | Reset the idle timer. |
"""


class ConciseResultsTests(unittest.TestCase):
    def setUp(self):
        self.cases = [{"variants": [{
            "id": "Q06-c", "title": "Idle release", "summary": "Checks the idle timer.",
        }]}]
        self.runs = [
            {"path": "runs/older", "results": [{
                "variant_id": "Q06-c", "observed_at": "2026-11-06T02:00:00Z",
                "status": "fail", "evidence": [],
            }]},
            {"path": "runs/newer", "results": [{
                "variant_id": "Q06-c", "observed_at": "2026-11-06T02:00:00.500Z",
                "status": "blocked", "evidence": ["evidence/screenshot.png", "report.md"],
            }]},
        ]

    def test_uses_latest_recorded_result_and_png_evidence(self):
        self.assertEqual([{
            "variant_id": "Q06-c", "tried": "Sent a follow-up.",
            "happened": "Claude replied.", "wanted": "Reset the idle timer.",
            "status": "blocked", "images": ["runs/newer/evidence/screenshot.png"],
        }], concise_results(REPORT, self.cases, self.runs))

    def test_new_result_without_report_row_remains_publishable(self):
        self.assertEqual([{
            "variant_id": "Q06-c", "tried": "Idle release.",
            "happened": "A blocked result was recorded; summary pending.",
            "wanted": "Checks the idle timer.", "status": "blocked",
            "images": ["runs/newer/evidence/screenshot.png"],
        }], concise_results("| Test | Tried | Happened | Wanted |", self.cases, self.runs))


if __name__ == "__main__":
    unittest.main()
