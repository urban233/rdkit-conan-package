"""Ensure missing or skipped tests cannot produce a successful acceptance report."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run


class ReportChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.artifacts = Path(self.directory.name)
        self.override = patch.object(run, "ARTIFACTS", self.artifacts)
        self.override.start()
        self.addCleanup(self.override.stop)

    def consumer(self, extra="", names=("core", "fingerprints", "suppliers", "conformers", "drawing", "cairo", "inchi")):
        cases = ''.join(f'<testcase name="{name}">{extra}</testcase>' for name in names)
        (self.artifacts / "test-consumer-tests.xml").write_text(f'<testsuite>{cases}</testsuite>')

    def test_missing_report_fails(self):
        with self.assertRaises(RuntimeError):
            run.verify_reports(False, True, True)

    def test_missing_upstream_report_fails(self):
        self.consumer()
        with self.assertRaises(RuntimeError):
            run.verify_reports(True, True, True)

    def test_empty_or_incomplete_report_fails(self):
        for names in ((), ("core",)):
            with self.subTest(names=names):
                self.consumer(names=names)
                with self.assertRaises(RuntimeError):
                    run.verify_reports(False, True, True)

    def test_failures_errors_and_skips_fail(self):
        for tag in ("failure", "error", "skipped"):
            with self.subTest(tag=tag):
                self.consumer(extra=f'<{tag}/>')
                with self.assertRaises(RuntimeError):
                    run.verify_reports(False, True, True)

    def test_complete_reports_pass(self):
        self.consumer()
        (self.artifacts / "test-upstream-tests.xml").write_text(
            '<testsuite><testcase name="upstream-example"/></testsuite>')
        (self.artifacts / "test-upstream-inventory.json").write_text(
            '{"tests":[{"name":"upstream-example"}]}')
        run.verify_reports(True, True, True)
        self.assertTrue((self.artifacts / "test-counts.json").is_file())

    def test_missing_discovered_test_fails(self):
        self.consumer()
        (self.artifacts / "test-upstream-tests.xml").write_text(
            '<testsuite><testcase name="upstream-example"/></testsuite>')
        (self.artifacts / "test-upstream-inventory.json").write_text(
            '{"tests":[{"name":"upstream-example"},{"name":"missing"}]}')
        with self.assertRaises(RuntimeError):
            run.verify_reports(True, True, True)


if __name__ == "__main__":
    unittest.main()
