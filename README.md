# RDKit Conan Package

[![License](https://img.shields.io/badge/license-BSD-blue.svg)](https://github.com/rdkit/rdkit/blob/master/LICENSE)
[![Conan](https://img.shields.io/badge/conan-ready-brightgreen.svg)](https://conan.io/)

This repository provides a **Conan package** for the [RDKit](https://github.com/rdkit/rdkit) library, allowing easy integration of RDKit into C++ and Python projects using the Conan C/C++ package manager.

---

## Table of Contents

* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Building the Package](#building-the-package)
* [Optional GPU Support](#optional-gpu-support)
* [Using the Package in Other Projects](#using-the-package-in-other-projects)
* [License](#license)

---

## Prerequisites

Before using this Conan package, ensure you have the following installed:

1. **Python** (≥3.8) – required for Conan and RDKit scripting.

   ```bash
   python --version
   ```
2. **Conan** (≥2.0) – the C/C++ package manager.
   Install via pip (in a virtual environment):

   ```bash
   pip install conan
   ```
3. **CMake** (≥3.20) – required to build RDKit.

   ```bash
   cmake --version
   ```
4. **Compiler** – a C++14 compatible compiler (e.g., GCC, Clang, MSVC).

---

## Installation

Clone this repository:

```bash
git clone https://github.com/urban233/rdkit-conan-package.git
cd rdkit-conan
```

---

## Building the Package

To build the RDKit Conan package locally:

```bash
conan create . rdkit/2025.09.03
```

This will build the RDKit library and create a local Conan package.

---

## Using the Package in Other Projects

Once the Conan package is created, you can use it in any project:

```bash
mkdir my_project && cd my_project
conan install rdkit/2025.09.03
```

Include the generated files in your CMake project:

```cmake
include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()
```

---

## License

This project is licensed under the **BSD License** – see the [LICENSE](https://github.com/rdkit/rdkit/blob/master/LICENSE) file for details.

---

✅ **Notes:**

* Always verify that your Python and Conan versions meet the minimum requirements.
