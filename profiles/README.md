# Conan Profiles
This Conan RDKit package repository contains multiple different 
`Conan` profiles that can be used to run certain build configurations.

Each major operating system (incl. Windows, macOS and Linux) have their own
folder.
The profiles that are available are:
- **release**: The standard **static** release configuration without running the CTest test.
- **release_java**: A SWIG Java bindings build configuration.
- **release_shared**: A configuration for building RDKit as a collection of **shared** libraries.
- **release_test**: A release configuration with active CTest branch. Only this configuration runs the cpp tests.
