"""Build packages and verify them on a separate, source-free runner."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"


def run(*arguments):
    print("+", " ".join(map(str, arguments)), flush=True)
    subprocess.run(list(map(str, arguments)), check=True)


def collect_reports():
    for directory in [Path(os.environ["CONAN_HOME"]), ROOT / "test_package" / "build"]:
        for name in ("upstream-tests.xml", "consumer-tests.xml"):
            for index, report in enumerate(directory.rglob(name)):
                shutil.copy2(report, ARTIFACTS / f"{directory.name}-{index}-{name}")


def verify_reports(upstream, cairo, inchi):
    consumers = list(ARTIFACTS.glob("*consumer-tests.xml"))
    if not consumers:
        raise RuntimeError("No consumer test report was produced")
    expected = {"core", "fingerprints", "conformers", "drawing"}
    if cairo:
        expected.add("cairo")
    if inchi:
        expected.add("inchi")
    upstream_reports = list(ARTIFACTS.glob("*upstream-tests.xml"))
    if upstream and not upstream_reports:
        raise RuntimeError("No upstream test report was produced")
    counts = {}
    for report in consumers + upstream_reports:
        cases = list(ET.parse(report).getroot().iter("testcase"))
        if not cases or any(case.find(tag) is not None for case in cases
                            for tag in ("failure", "error", "skipped")):
            raise RuntimeError(f"Empty, failing, or skipped tests in {report}")
        if report in consumers and {case.attrib["name"] for case in cases} != expected:
            raise RuntimeError(f"Unexpected consumer test inventory in {report}")
        counts[report.name] = len(cases)
    (ARTIFACTS / "test-counts.json").write_text(json.dumps(counts, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=("build", "consume"))
    parser.add_argument("--variant", choices=("static", "shared", "java", "minimal"), required=True)
    args = parser.parse_args()
    ARTIFACTS.mkdir(exist_ok=True)
    shared, java, minimal = (args.variant == name for name in ("shared", "java", "minimal"))
    options = ["-o:h", f"rdkit/*:shared={shared}", "-o:h", f"rdkit/*:with_java={java}",
               "-o:h", f"rdkit/*:with_ctest={not java}",
               "-o:h", f"rdkit/*:with_cairo={not minimal}",
               "-o:h", f"rdkit/*:with_inchi={not minimal}"]
    profiles = ["-pr:h", "default", "-pr:b", "default"]
    try:
        if args.phase == "build":
            graph = ARTIFACTS / "create.json"
            run("conan", "create", ROOT, *profiles, *options, "--build=missing", "--build=rdkit/*",
                "-c:h", "tools.system.package_manager:mode=install",
                "-c:h", "tools.system.package_manager:sudo=True",
                "--format=json", f"--out-file={graph}")
            data = json.loads(graph.read_text())
            packages = [node for node in data["graph"]["nodes"].values()
                        if node.get("name") == "rdkit" and node.get("context") == "host"]
            if len(packages) != 1 or packages[0].get("binary") != "Build":
                raise RuntimeError("The current RDKit recipe was not built")
            (ARTIFACTS / "reference.txt").write_text(packages[0]["ref"] + "\n")
            run("conan", "list", f"--graph={graph}", "--graph-context=host-only",
                "--format=json", f"--out-file={ARTIFACTS / 'packages.json'}")
            run("conan", "cache", "save", f"--list={ARTIFACTS / 'packages.json'}", "--no-source",
                f"--file={ARTIFACTS / 'packages.tgz'}")
        else:
            run("conan", "cache", "restore", ARTIFACTS / "packages.tgz")
            run("conan", "test", ROOT / "test_package", (ARTIFACTS / "reference.txt").read_text().strip(),
                *profiles, *options, "--build=never", "--no-remote",
                "-c:h", "tools.system.package_manager:mode=install",
                "-c:h", "tools.system.package_manager:sudo=True")
    finally:
        collect_reports()
    verify_reports(args.phase == "build" and not java, not minimal, not minimal)
    (ARTIFACTS / "acceptance.json").write_text(json.dumps({
        "phase": args.phase, "variant": args.variant, "java": java, "success": True,
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
