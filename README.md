# RDKit Conan Package

[![Package acceptance](https://github.com/urban233/rdkit-conan-package/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/urban233/rdkit-conan-package/actions/workflows/ci.yml)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)

Build [RDKit](https://github.com/rdkit/rdkit) as a Conan 2 package for C++ applications, with optional Java bindings. This checkout packages **RDKit 2026.09.1**.

The workflow is: **build the recipe into your local Conan cache → install it in your application → link the generated CMake targets**. Cloning the repository or downloading a GitHub release does not install a Conan binary package.

- [Quick start](#quick-start)
- [Use RDKit from C++](#use-rdkit-from-c)
- [Build and use the Java bindings](#build-and-use-the-java-bindings)
- [Package options](#package-options)
- [What static means on Windows](#what-static-means-on-windows)
- [Profiles and reproducible builds](#profiles-and-reproducible-builds)
- [What CI verifies](#what-ci-verifies)
- [Troubleshooting](#troubleshooting)
- [For Coding Agents](#for-coding-agents)
- [License](#license)

## Quick start

### 1. Set up the tools

Install Python 3.11 or newer and a native C++20 compiler. On Windows, use an x64 Visual Studio developer command prompt with the C++ tools available. On macOS, install the Xcode command-line tools; on Linux, install a C++ compiler and its development tools.

Clone the repository and create a Python environment:

```sh
git clone https://github.com/urban233/rdkit-conan-package.git
cd rdkit-conan-package
python -m venv .venv
```

Activate it on Linux/macOS:

```sh
. .venv/bin/activate
```

Or in the Windows developer command prompt:

```bat
.venv\Scripts\activate.bat
```

Install the same build tools used by CI:

```sh
python -m pip install conan==2.34.0 cmake==3.31.10 ninja==1.13.0
```

Java builds also need **JDK 17**, with `JAVA_HOME` pointing to the JDK and `java` and `javac` on `PATH`. Conan supplies SWIG when Java bindings are enabled.

### 2. Check your compiler profile

On a new Conan installation, detect the native compiler:

```sh
conan profile detect
```

If a `default` profile already exists, inspect it instead of overwriting it:

```sh
conan profile show -pr:h default -pr:b default
```

Check that the OS, architecture, compiler version, and C++ standard library match your toolchain. The commands below select C++20 and Release explicitly.

### 3. Build and test the package

Run from this repository's root:

```sh
conan create . --build=missing -pr:h default -pr:b default -s:h build_type=Release -s:h compiler.cppstd=20 -c tools.build:jobs=2
```

This downloads RDKit and its dependencies, builds a static package, runs upstream C++ tests, and builds and runs the installed-package consumers. The first build can take an hour or longer. `tools.build:jobs=2` limits build parallelism; adjust it for your machine.

The result is **`rdkit/2026.09.1` in your local Conan cache**. No system-wide RDKit installation is needed. To check the version of another checkout, run `conan inspect .`. Published [releases](https://github.com/urban233/rdkit-conan-package/releases) identify recipe revisions for older versions; check out the corresponding tag before building and use that version in your application.

## Use RDKit from C++

After creating the package, make a separate application directory containing these three files. The example prints `CCO`.

**`conanfile.txt`**

```ini
[requires]
rdkit/2026.09.1

[generators]
CMakeDeps
CMakeToolchain
VirtualRunEnv
```

**`CMakeLists.txt`**

```cmake
cmake_minimum_required(VERSION 3.21)
project(rdkit_example LANGUAGES CXX)

find_package(RDKit CONFIG REQUIRED)

add_executable(rdkit_example main.cpp)
target_compile_features(rdkit_example PRIVATE cxx_std_20)
target_link_libraries(rdkit_example PRIVATE RDKit::SmilesParse)
```

**`main.cpp`**

```cpp
#include <GraphMol/SmilesParse/SmilesParse.h>
#include <GraphMol/SmilesParse/SmilesWrite.h>
#include <iostream>
#include <memory>

int main() {
    std::unique_ptr<RDKit::RWMol> molecule(RDKit::SmilesToMol("OCC"));
    if (!molecule) {
        return 1;
    }
    std::cout << RDKit::MolToSmiles(*molecule) << '\n';
}
```

Install dependencies and build from the application directory, with the Python environment still active:

```sh
conan install . --output-folder=build --build=never -pr:h default -pr:b default -s:h build_type=Release -s:h compiler.cppstd=20 -c tools.cmake.cmaketoolchain:generator=Ninja
cmake -S . -B build -G Ninja -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

Activate Conan's generated runtime environment before running the application. It supplies library search paths and RDKit's packaged data location (`RDBASE`/`RDBase`).

Linux/macOS:

```sh
. ./build/conanrun.sh
./build/rdkit_example
```

Windows developer command prompt:

```bat
build\conanrun.bat
build\rdkit_example.exe
```

Link the components your code uses, such as `RDKit::FileParsers`, `RDKit::Fingerprints`, `RDKit::SubstructMatch`, or `RDKit::MolDraw2D`. Their targets carry transitive libraries, include paths, and public compile definitions. See [the consumer CMake file](test_package/CMakeLists.txt) for working combinations. Avoid manually listing RDKit libraries or copying compiler definitions from another installation.

For shared libraries, first create the package with `-o:h "rdkit/*:shared=True"`, then pass the same option to `conan install`. Keep the runtime environment active when launching the application. Windows users should also read [what static means on Windows](#what-static-means-on-windows).

## Build and use the Java bindings

With JDK 17 configured, run from the repository root:

```sh
conan create . --build=missing -pr:h default -pr:b default -s:h build_type=Release -s:h compiler.cppstd=20 -o:h "rdkit/*:with_java=True" -o:h "rdkit/*:with_ctest=False" -o:h "rdkit/*:shared=False" -c tools.build:jobs=2
```

This matches CI's Java configuration: static RDKit libraries inside a native JNI wrapper. Upstream C++ tests are disabled in this configuration; the installed-package C++ tests and the Java compile/runtime test still run.

Find the Java-enabled package ID in the `conan create` output or list its configuration:

```sh
conan list "rdkit/2026.09.1:*"
conan cache path "rdkit/2026.09.1:<package-id>"
```

Replace `<package-id>` with the ID whose options include `with_java=True`, `with_ctest=False`, and `shared=False`. The returned package folder contains:

| Artifact | Location inside the package |
| --- | --- |
| Java classes | `share/java/org.RDKit.jar` |
| Windows JNI wrapper | `bin/GraphMolWrap.dll` |
| Linux JNI wrapper | `bin/libGraphMolWrap.so` |
| macOS JNI wrapper | `bin/libGraphMolWrap.jnilib` or `bin/libGraphMolWrap.dylib` |
| RDKit runtime data | `share/RDKit` |

In your Java application directory, generate a runtime environment for the same package configuration:

```sh
conan install --requires=rdkit/2026.09.1 --output-folder=java-env --build=never -pr:h default -pr:b default -s:h build_type=Release -s:h compiler.cppstd=20 -o:h "rdkit/*:with_java=True" -o:h "rdkit/*:with_ctest=False" -o:h "rdkit/*:shared=False" -g VirtualRunEnv
```

Activate `java-env/conanrun.sh` on Linux/macOS or `java-env\conanrun.bat` in the Windows developer command prompt, as in the C++ example. Save this as **`HelloRDKit.java`**:

```java
import org.RDKit.RWMol;

public final class HelloRDKit {
    public static void main(String[] args) {
        System.loadLibrary("GraphMolWrap");
        RWMol molecule = RWMol.MolFromSmiles("OCC");
        if (molecule == null) {
            throw new IllegalArgumentException("Invalid SMILES");
        }
        try {
            System.out.println(molecule.MolToSmiles());
        } finally {
            molecule.delete();
        }
    }
}
```

Replace `<package-folder>` below with the cache path reported above. Compile on any platform:

```sh
javac -cp "<package-folder>/share/java/org.RDKit.jar" HelloRDKit.java
```

Run on Linux/macOS:

```sh
java "-Djava.library.path=<package-folder>/bin" -cp ".:<package-folder>/share/java/org.RDKit.jar" HelloRDKit
```

On Windows, use `;` as the classpath separator:

```bat
java "-Djava.library.path=<package-folder>/bin" -cp ".;<package-folder>/share/java/org.RDKit.jar" HelloRDKit
```

Both examples should print `CCO`. The [CI Java consumer](test_package/java/PackageSmoke.java) also exercises fingerprints. The JAR and native wrapper must come from the same package; do not mix them with a separate RDKit installation. For application distribution, copy the required runtime artifacts into your application's deployment layout rather than depending on a developer's Conan cache path.

## Package options

Set options with `-o:h "rdkit/*:option=value"` on both package creation and application installation.

| Option | Default | Meaning |
| --- | --- | --- |
| `shared` | `False` | Build static RDKit and Boost libraries; set `True` for shared libraries. This option does not select the MSVC runtime; see [Windows linkage](#what-static-means-on-windows). |
| `with_ctest` | `True` | Build and execute the upstream C++ tests during package creation. |
| `with_java` | `False` | Build the Java JAR and JNI wrapper; requires JDK 17. CI tests this with `shared=False` and `with_ctest=False`. |
| `with_cairo` | `True` | Enable Cairo drawing support. |
| `with_inchi` | `True` | Enable InChI support. |
| `with_eigen` | `True` | Required; setting `False` is rejected. |
| `with_python` | `False` | Python bindings are unsupported; setting `True` is rejected. |
| `with_csharp` | `False` | C# bindings are unsupported; setting `True` is rejected. |

`with_ctest=False` does not disable the separate `test_package` consumers run by `conan create`. CI also tests a Linux package with both `with_cairo=False` and `with_inchi=False`.

## What static means on Windows

With `-o:h "rdkit/*:shared=False"`, **RDKit and Boost are static libraries, while the tested MSVC runtime is dynamic (`/MD`)**. Library linkage and runtime linkage are separate settings.

| Part | Windows static configuration tested by CI |
| --- | --- |
| RDKit | Static `.lib` archives; no RDKit DLLs are needed. |
| Boost | Static `.lib` archives; no Boost DLLs are needed. The recipe explicitly makes Boost's `shared` option follow RDKit's. |
| Other production dependencies, such as Cairo, FreeType, and zlib | Static in the default resolved CI graph. Their linkage remains controlled by their own Conan options. |
| MSVC C/C++ runtime | Dynamic: `compiler.runtime=dynamic`, `compiler.runtime_type=Release`, corresponding to `/MD`. Microsoft runtime DLLs are still required. |
| Java bindings | `GraphMolWrap.dll` remains a JNI DLL, with RDKit and Boost linked statically into it. |

RDKit and Boost remain separate archives until the final application or JNI wrapper is linked. Use the generated `RDKit::...` CMake targets to supply the required libraries and definitions. Conan disables Boost auto-linking with `BOOST_ALL_NO_LIB`; avoid mixing in libraries or headers from a separate Boost installation.

The tested C++ executable and Java wrapper import Microsoft runtime DLLs such as `MSVCP140.dll` and `VCRUNTIME140.dll`, along with Windows system DLLs. A static RDKit package therefore still has runtime DLL dependencies.

Keep the application and its dependencies consistent in architecture, compatible MSVC toolchain, Release/Debug configuration, and runtime choice. **`shared=False` does not select `/MT`** (the static MSVC runtime), and `/MT` is not covered by the current CI matrix. See [Microsoft's `/MD` and `/MT` documentation](https://learn.microsoft.com/en-us/cpp/build/reference/md-mt-ld-use-run-time-library?view=msvc-170) for the runtime distinction.

## Profiles and reproducible builds

The examples use your detected native compiler profile. The checked-in [profiles](profiles/README.md) are starting points with fixed compiler versions and architectures; review them before use. CI detects each runner's native compiler rather than using those fixed profiles.

- Keep host and build profiles explicit (`-pr:h` and `-pr:b`), and match the package's compiler, C++ standard library, build type, architecture, and options in consumers.
- Pin the RDKit version in your application. For repeatable dependency resolution, also keep an application Conan lockfile; for exact binary reproduction, retain the profiles, dependency revisions, and toolchain versions.
- Use generated `RDKit::...` CMake targets and the runtime environment. RDKit feature definitions affect C++ class layouts as well as available functionality.
- Keep package builds in the Conan cache. Avoid adding source-tree include paths or build-tree libraries to consumers.

Conan's [CMakeDeps](https://docs.conan.io/2/reference/tools/cmake/cmakedeps.html), [CMakeToolchain](https://docs.conan.io/2/reference/tools/cmake/cmaketoolchain.html), and [VirtualRunEnv](https://docs.conan.io/2/reference/tools/env/virtualrunenv.html) documentation describes the generated integration files.

## What CI verifies

The [Package acceptance workflow](https://github.com/urban233/rdkit-conan-package/actions/workflows/ci.yml) requires **ten builds and ten independent consumer jobs**:

| Platform | Static C++ | Shared C++ | Java | Cairo/InChI disabled |
| --- | --- | --- | --- | --- |
| Windows x86-64 | yes | yes | yes | |
| Linux x86-64 | yes | yes | yes | yes |
| macOS ARM64 | yes | yes | yes | |

Native builds execute upstream tests. Consumers exercise parsing, suppliers, fingerprints, conformers, drawing, packaged data, enabled InChI/Cairo features, and Java native loading. A second runner consumes each package from a relocated cache with `--build=never --no-remote`, without source or build directories.

The required **`ci-required`** gate checks every job and the complete test evidence. Empty suites, missing or skipped tests, incorrect linkage, and missing matrix configurations fail the gate. Configure branch protection to require this check. See [CI acceptance testing](ci/README.md) for local reproduction and diagnostic artifacts.

This coverage is for Release builds on the platforms above. Debug builds, cross-compilation, other architectures, and other compiler versions are not covered by this matrix.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `rdkit/...` is missing or Conan reports a missing binary | Run `conan create .` for that version and configuration first. Compare host profiles, build type, and options; `--build=never` intentionally prevents silently rebuilding a different package. |
| CMake cannot find RDKit | Run `conan install` in the application directory and configure with its generated `conan_toolchain.cmake`. |
| A dependency reports missing system development packages | Install the packages listed in Conan's system-requirements diagnostic, then rerun the build. |
| A shared library or JNI wrapper cannot be loaded | Activate the matching `conanrun` environment. For Java, also set `java.library.path` to the package's `bin` directory and use the matching JAR. |
| RDKit cannot find parameter/data files | Use the generated runtime environment so `RDBASE` and `RDBase` refer to packaged `share/RDKit`, rather than an RDKit source checkout. |
| The compiler differs from a checked-in profile | Use a detected native profile or adapt the fixed profile to the installed toolchain. Do not label one compiler version as another. |

## For Coding Agents

Use the recipe and executable tests as the source of truth. Start with these files:

| Area | Files |
| --- | --- |
| Version, options, dependencies, source adaptations, packaging | [conanfile.py](conanfile.py) |
| Upstream CMake integration and component metadata | [cmake/](cmake/) |
| Installed-package C++ and Java behavior | [test_package/](test_package/) |
| Build/consume orchestration and evidence checks | [ci/run.py](ci/run.py), [ci/check_matrix.py](ci/check_matrix.py), [ci/README.md](ci/README.md) |
| Matrix, triggers, and pinned tools | [ci.yml](.github/workflows/ci.yml), [setup action](.github/actions/setup/action.yml) |

When changing this repository:

1. **Keep the change focused.** Inspect the working tree first and preserve existing work. Use a separate branch for each RDKit version. Keep the recipe version, README examples, and CI documentation consistent, and link the exact upstream release in the PR.
2. **Audit source adaptations against the exact upstream tag.** Verify every `replace_in_file` match, check whether upstream has fixed the issue, and remove obsolete adaptations. Keep runtime dependencies separate from test-only dependencies.
3. **Preserve the consumer interface.** Export public compile definitions and transitive dependencies through Conan component metadata. Verify static/shared selection, installed headers, data files, and Java artifacts. Fix class-layout or linkage problems at their source rather than adding flags only to the test application.
4. **Use isolated build state.** Set `CONAN_HOME` to a fresh writable directory when reproducing CI, use matching native profiles, and keep a second empty cache for the consume phase. Follow [the local CI instructions](ci/README.md#running-locally). Do not delete or relabel the user's default cache or compiler profile to make a build pass.
5. **Validate at the appropriate level.** Start with the lightweight checks below. Recipe, CMake integration, packaging, and runtime changes then need the full acceptance matrix. Graph resolution or a successful compile alone does not establish a working package. Documentation-only changes need their commands, paths, links, and examples checked against the current recipe.
6. **Keep CI evidence strict.** Do not shrink the matrix, suppress failures, skip failing tests, add retries to hide failures, or loosen the inventory/linkage checks. Inspect the uploaded JUnit reports and package graphs when a job fails. PRs run automatically; use manual workflow dispatch to test a branch before opening a PR.
7. **Report what was actually verified.** State the configuration and results, link the CI run, and identify checks that remain pending. A green `ci-required` is required before merging package changes. Publish a version's release only after its PR is merged and `main` CI passes; link upstream and target the tested version commit rather than a moving branch.

Run the lightweight report/matrix checks from the repository root:

```sh
python -m unittest discover -s ci -p 'test_*.py'
```

These checks validate CI's report handling; they do not build or test RDKit itself.

## License

This repository uses the [BSD 3-Clause License](LICENSE). RDKit's upstream license is included in each package under `licenses/license.txt`; dependencies retain their own licenses.
