# Package acceptance testing

The `Package acceptance` workflow tests RDKit 2025.09.3. A successful run requires
all ten build configurations and their ten independent consumer jobs to pass:

| Platform | Static | Shared | Java | Cairo/InChI disabled |
| --- | --- | --- | --- | --- |
| Windows x86-64 | yes | yes | yes | |
| Linux x86-64 | yes | yes | yes | yes |
| macOS ARM64 | yes | yes | yes | |

Native builds run upstream CTest tests. Every configuration builds and executes
separate C++ consumers for SMILES parsing, canonicalization, substructure matching,
fingerprints, conformer generation/MMFF optimization, SVG drawing, and enabled
Cairo/InChI features. Java builds additionally compile and run a JVM consumer using
the packaged JAR and native wrapper. Test checks remain active in Release builds.

The consumer jobs restore packages into a new cache on a fresh runner and repeat
the consumer tests with `--build=never --no-remote`. The transfer archive excludes
sources and build directories. Only packaged data files and Conan's runtime
environment are available to the consumers. Dependencies are transferred with
their exact recipe and binary revisions.

Empty test suites, missing consumer tests, failures, and skipped tests are errors.
Upstream execution must match CTest's discovered test inventory. Native binary
dependencies must match the requested static/shared linkage.
There are no automatic test retries or expected-failure exclusions. JUnit reports,
test counts, and resolved package graphs are uploaded even when a job fails.
Weekly runs check whether changes in dependency recipes or runner images affect
the package. Native compiler profiles are detected on each runner; Conan, CMake,
Ninja, Python, and the JDK use explicit versions in the setup action.

Configure branch protection to require the uniquely named `ci-required` check.
It rejects failed, cancelled, and unexpectedly skipped build/consumer jobs.
It also requires separate acceptance evidence for all twenty expected
platform/configuration/phase combinations, so an accidentally reduced matrix
cannot pass the final check.
The workflow runs on pull requests, pushes to `main` and `feat/**`, weekly, and
through manual workflow dispatch. No publishing or release steps are included.

## Running locally

Install the versions listed in `.github/actions/setup/action.yml`, and a native
compiler. Java configurations also require JDK 17 on `PATH` with `JAVA_HOME` set.
Choose a fresh writable directory for `CONAN_HOME`, then run:

```sh
conan profile detect --force
python ci/run.py build --variant static
```

The variants are `static`, `shared`, `java`, and `minimal`. To repeat consumption,
retain `artifacts/packages.tgz` and `artifacts/reference.txt`, set `CONAN_HOME` to a
different empty directory, detect a matching compiler profile, and run:

```sh
python ci/run.py consume --variant static
```

The lightweight report-validation checks run with:

```sh
python -m unittest discover -s ci -p 'test_*.py'
```

Python and C# bindings and disabling Eigen are explicitly unsupported. This CI
does not claim Debug, cross-compilation, other architectures, or other compiler
versions are validated. Future supported RDKit releases must enter the same
acceptance matrix before being documented as supported.
