import os
import shlex
from pathlib import Path

from conan import ConanFile
from conan.tools.build import can_run
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout


class PackageAcceptance(ConanFile):
    settings = "os", "compiler", "build_type", "arch"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def generate(self):
        dependency = self.dependencies["rdkit"]
        toolchain = CMakeToolchain(self)
        toolchain.variables["EXPECTED_RDKIT_VERSION"] = str(dependency.ref.version)
        toolchain.variables["TEST_CAIRO"] = bool(dependency.options.with_cairo)
        toolchain.variables["TEST_INCHI"] = bool(dependency.options.with_inchi)
        toolchain.generate()
        CMakeDeps(self).generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not can_run(self):
            raise RuntimeError("Acceptance tests require a native runner")
        self.run(f"ctest --test-dir . -C {self.settings.build_type} --output-on-failure "
                 "--no-tests=error --output-junit consumer-tests.xml --timeout 120",
                 cwd=self.build_folder, env="conanrun")
        dependency = self.dependencies["rdkit"]
        package = Path(dependency.package_folder)
        if not (package / "licenses" / "license.txt").is_file():
            raise RuntimeError("Package is missing its license")
        if not (package / "share" / "RDKit" / "Data" / "BaseFeatures.fdef").is_file():
            raise RuntimeError("Package is missing RDKit runtime data")
        if dependency.options.with_java:
            jar = package / "share" / "java" / "org.RDKit.jar"
            native = list((package / "bin").glob("*GraphMolWrap.*"))
            if not jar.is_file() or not native:
                raise RuntimeError("Package is missing its Java bindings")
            def quote(path):
                return '"' + str(path) + '"' if self.settings.os == "Windows" else shlex.quote(str(path))
            classes = Path(self.build_folder) / "java-classes"
            classes.mkdir(exist_ok=True)
            source = Path(self.source_folder) / "java" / "PackageSmoke.java"
            self.run(f"javac -cp {quote(jar)} -d {quote(classes)} {quote(source)}", env="conanrun")
            classpath = str(classes) + os.pathsep + str(jar)
            self.run(f"java -Djava.library.path={quote(package / 'bin')} -cp {quote(classpath)} "
                     "PackageSmoke", env="conanrun")
