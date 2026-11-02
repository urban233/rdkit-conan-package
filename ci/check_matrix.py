"""Require evidence for every supported configuration before CI can pass."""
import json
from pathlib import Path
import sys


def verify(directory):
    configurations = {(os_name, arch, variant)
                      for os_name, arch in (("Windows", "X64"), ("Linux", "X64"), ("macOS", "ARM64"))
                      for variant in ("static", "shared", "java")}
    configurations.add(("Linux", "X64", "minimal"))
    expected = {(*configuration, phase) for configuration in configurations for phase in ("build", "consume")}
    observed = set()
    for path in directory.rglob("acceptance.json"):
        report = json.loads(path.read_text())
        key = (report["os"], report["arch"], report["variant"], report["phase"])
        if report["success"] is not True or key in observed:
            raise RuntimeError(f"Failed or duplicate acceptance evidence: {path}")
        observed.add(key)
    if observed != expected:
        raise RuntimeError(f"Acceptance matrix mismatch. Missing: {expected - observed}; unexpected: {observed - expected}")
    print(f"All {len(expected)} build/consumer configurations passed")


if __name__ == "__main__":
    verify(Path(sys.argv[1]))
