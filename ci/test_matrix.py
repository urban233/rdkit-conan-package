import json
from pathlib import Path
import tempfile
import unittest

from check_matrix import verify


class MatrixChecks(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        for os_name, arch in (("Windows", "X64"), ("Linux", "X64"), ("macOS", "ARM64")):
            variants = ("static", "shared", "java", "minimal") if os_name == "Linux" else ("static", "shared", "java")
            for variant in variants:
                for phase in ("build", "consume"):
                    directory = self.root / f"{os_name}-{variant}-{phase}"
                    directory.mkdir()
                    (directory / "acceptance.json").write_text(json.dumps({
                        "os": os_name, "arch": arch, "variant": variant,
                        "phase": phase, "success": True,
                    }))

    def test_complete_matrix_passes(self):
        verify(self.root)

    def test_missing_configuration_fails(self):
        next(self.root.rglob("acceptance.json")).unlink()
        with self.assertRaises(RuntimeError):
            verify(self.root)

    def test_duplicate_evidence_fails(self):
        duplicate = self.root / "duplicate"
        duplicate.mkdir()
        (duplicate / "acceptance.json").write_text(next(self.root.rglob("acceptance.json")).read_text())
        with self.assertRaises(RuntimeError):
            verify(self.root)

    def test_wrong_architecture_fails(self):
        report = next(self.root.rglob("acceptance.json"))
        data = json.loads(report.read_text())
        data["arch"] = "unexpected"
        report.write_text(json.dumps(data))
        with self.assertRaises(RuntimeError):
            verify(self.root)


if __name__ == "__main__":
    unittest.main()
