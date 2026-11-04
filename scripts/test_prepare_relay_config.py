#!/usr/bin/env python3
"""Check that local Relay rendering never stores credential values."""

import json
import runpy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

MODULE = runpy.run_path(str(Path(__file__).with_name("prepare-relay-config.py")))


class RelayConfigTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.baseline = json.loads(MODULE["SOURCE"].read_text())
        self.source = Path(self.temp.name) / "baseline.json"
        self.patcher = patch.dict(MODULE["render"].__globals__, {"SOURCE": self.source})
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def test_loopback_ports_and_no_inline_credentials(self):
        self.source.write_text(json.dumps(self.baseline))
        rendered = json.loads(MODULE["render"]())
        self.assertEqual("127.0.0.1:22112", rendered["prometheusAddress"])
        self.assertEqual("127.0.0.1:22113", rendered["statusUIAddress"])
        for name in ("claudeCodeRunnerPools", "cursorWorkerPools"):
            self.assertNotIn("secret", rendered[name][0])
            self.assertIn("secret_env", rendered[name][0])

    def test_inline_secret_rejected(self):
        self.baseline["config"]["claudeCodeRunnerPools"][0]["secret"] = "uncommitted-test-value"
        self.source.write_text(json.dumps(self.baseline))
        with self.assertRaisesRegex(ValueError, "only secret_env"):
            MODULE["render"]()

    def test_other_org_rejected(self):
        self.baseline["config"]["cursorWorkerPools"][0]["organization"] = "coder"
        self.source.write_text(json.dumps(self.baseline))
        with self.assertRaisesRegex(ValueError, "steven QA template"):
            MODULE["render"]()


if __name__ == "__main__":
    unittest.main()
