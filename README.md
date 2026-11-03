# RDKit Conan Package

[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://github.com/rdkit/rdkit/blob/master/LICENSE)
[![Conan](https://img.shields.io/badge/conan-ready-brightgreen.svg)](https://conan.io/)

This repository provides a **Conan package** for the [RDKit](https://github.com/rdkit/rdkit) library, with C++ libraries and optional Java bindings.

---

## Table of Contents

* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Building the Package](#building-the-package)
* [Using the Package in Other Projects](#using-the-package-in-other-projects)
* [Building the SWIG Java bindings](#Building-the-SWIG-Java-bindings)
* [Conan Profiles](#Conan-Profiles)
* [License](#license)

---

## Prerequisites

Automated package and runtime checks are described in [CI acceptance testing](ci/README.md).
Python and C# bindings are currently unsupported by this recipe. Java and native
C++ packages are tested on Windows, Linux, and macOS.

Before using this Conan package, ensure you have the following installed:

1. **Python** (≥3.11) – required for the tested Conan toolchain and scripting.

   ```bash
   python --version
   ```
2. **Conan** (2.34.0 tested) – the C/C++ package manager.
   Install via pip (in a virtual environment):

   ```bash
   pip install conan==2.34.0
   ```
3. **CMake** (≥3.21; 3.31.10 tested) – required to build RDKit and write JUnit test reports.

   ```bash
   cmake --version
   ```
4. **Compiler** – a C++20 compatible compiler (e.g., GCC, Clang, MSVC).

---

## Installation

Clone this repository:

```bash
git clone https://github.com/urban233/rdkit-conan-package.git
cd rdkit-conan-package
```

---

## Building the Package

To build the RDKit Conan package locally:

```bash
conan profile detect --force
conan create . --build=missing -s:h compiler.cppstd=20
```

This will build the RDKit library and create a local Conan package.

---

## Using the Package in Other Projects

Once the Conan package is created, you can use it in any project:

```bash
mkdir my_project && cd my_project
conan install --requires=rdkit/2025.09.6 --build=missing -s:h compiler.cppstd=20 -g CMakeDeps -g CMakeToolchain
```

Include the generated files in your CMake project:

```cmake
find_package(RDKit REQUIRED)
```

A good starting point, on how to use this Conan package is the 
[rdkit-cpp-example-template](https://github.com/urban233/rdkit-conan-package) GitHub repository.

---

## Building the SWIG Java bindings

With this Conan package it is also possible to build the Java SWIG bindings 
(probably also the C# SWIG bindings but that has not been tested yet).

To build the Java bindings run the build command with the `release_java` `Conan` profile.
After you've cloned the repository run the following shell commands:
```shell
conan source
conan install . --build=missing --profile profiles/<os>/release_java
conan build . --profile profiles/<os>/release_java
```
or simply
```shell
conan create . --build=missing -pr:h profiles/<os>/release_java -pr:b default
```

A good starting point, on how to use this Conan package is the 
[rdkit-kotlin-example-template](https://github.com/urban233/rdkit-kotlin-example-template) 
and 
[rdkit-java-example-template](https://github.com/urban233/rdkit-java-example-template)
GitHub repository.

### Windows
After the build process finished, you can access the `GraphMolWrap.dll` under
```shell
rdkit-conan-package\src\build\Code\JavaWrappers\gmwrapper\Release\GraphMolWrap.dll
```
and the JavaDoc API documentation under:
```shell
rdkit-conan-package\src\Code\JavaWrappers\gmwrapper\doc\org\RDKit
```

### macOS
The `libGraphMolWrap.jnilib` will be placed under a similar directory, maybe
something like: 
```shell
rdkit-conan-package\src\build\Code\JavaWrappers\gmwrapper\libGraphMolWrap.jnilib
```
and the JavaDoc API documentation under:
```shell
rdkit-conan-package\src\Code\JavaWrappers\gmwrapper\doc\org\RDKit
```

**NOTE**: This is **not** tested!

### Linux
The `libGraphMolWrap.so` will be placed under a similar directory, maybe
something like:
```shell
rdkit-conan-package\src\build\Code\JavaWrappers\gmwrapper\libGraphMolWrap.jnilib
```
and the JavaDoc API documentation under:
```shell
rdkit-conan-package\src\Code\JavaWrappers\gmwrapper\doc\org\RDKit
```

**NOTE**: This is **not** tested!

---

## Conan Profiles
More information about each `Conan` profile can be accessed under the 
`README.md` file in the `profiles/` folder.

---

## License

This project is licensed under the **BSD License** – see the [LICENSE](https://github.com/rdkit/rdkit/blob/master/LICENSE) file for details.
