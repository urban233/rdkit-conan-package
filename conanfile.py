import os
import shutil

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import get

class RDKitConan(ConanFile):
  name = "rdkit"
  version = "2025.09.3"
  license = "BSD-3-Clause"
  url = "https://github.com/rdkit/rdkit"
  description = "The RDKit is a collection of cheminformatics and machine-learning software written in C++ and Python."
  topics = ("chemistry", "cheminformatics", "c++", "python", "molecule")

  settings = "os", "compiler", "build_type", "arch"
  options = {
    "shared": [True, False],
    "with_python": [True, False],
    "with_inchi": [True, False],
    "with_cairo": [True, False],
    "with_eigen": [True, False],
    "with_ctest": [True, False],
  }
  default_options = {
    "shared": False,
    "with_python": False,
    "with_inchi": True,
    "with_cairo": True,
    "with_eigen": True,
    "with_ctest": False,
  }

  exports_sources = "CMakeLists.txt"

  def source(self):
    get(self,
        url=f"https://github.com/rdkit/rdkit/archive/refs/tags/Release_{self.version.replace('.', '_')}.zip",
        strip_root=True)
    # fixme: A .patch file would be the more elegant solution
    shutil.copyfile(
      os.path.join(
        self.export_sources_folder, "CMakeLists.txt"
      ),
      os.path.join(
        self.source_folder, "CMakeLists.txt"
      )
    )

  def layout(self):
    cmake_layout(
      self,
      src_folder="src",
      build_folder="src/build"
    )

  def configure(self):
    if self.options.shared:
      self.options.rm_safe("fPIC")

    # Propagate options to Boost here so the correct binary is downloaded/built
    self.options["boost"].shared = True
    self.options["boost"].without_iostreams = False
    self.options["boost"].without_zlib = False
    self.options["boost"].without_serialization = False # RDKit usually needs this too
    self.options["boost"].without_system = False

  def generate(self):
    # CMake toolchain
    tc = CMakeToolchain(self)
    # Mirrors .azure-pipelines/vs_build_dll.yml
    tc.variables["CMAKE_BUILD_TYPE"] = "Release"
    tc.variables["RDK_INSTALL_INTREE"] = "ON"
    tc.variables["RDK_INSTALL_STATIC_LIBS"] = "OFF"
    tc.variables["RDK_INSTALL_DLLS_MSVC"] = "ON"
    tc.variables["RDK_BUILD_CPP_TESTS"] = "ON"
    tc.variables["RDK_BUILD_PYTHON_WRAPPERS"] = "OFF"
    tc.variables["RDK_BUILD_COORDGEN_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_MAEPARSER_SUPPORT"] = "ON"
    tc.variables["RDK_OPTIMIZE_POPCNT"] = "ON"
    tc.variables["RDK_BUILD_TEST_GZIP"] = "ON"
    tc.variables["RDK_BUILD_FREESASA_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_AVALON_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_INCHI_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_YAEHMOP_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_XYZ2MOL_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_CAIRO_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_THREADSAFE_SSS"] = "ON"
    tc.variables["RDK_BUILD_SWIG_WRAPPERS"] = "OFF"
    tc.variables["RDK_SWIG_STATIC"] = "OFF"
    tc.variables["RDK_TEST_MULTITHREADED"] = "ON"

    # 1. Remove MSVC runtime enforcement (use default VS runtime)
    if "CMAKE_MSVC_RUNTIME_LIBRARY" in tc.cache_variables:
      del tc.cache_variables["CMAKE_MSVC_RUNTIME_LIBRARY"]

    # 2. Remove parallel /MP flags added by Conan
    tc.cache_variables.pop("CONAN_CXX_FLAGS", None)
    tc.cache_variables.pop("CONAN_C_FLAGS", None)

    tc.generate()

    # CMakeDeps for dependencies
    deps = CMakeDeps(self)

    # Eigen
    deps.set_property("eigen", "cmake_file_name", "Eigen3")
    deps.set_property("eigen", "cmake_target_name", "Eigen3::Eigen")
    tc.cache_variables["EIGEN3_FOUND"] = True

    # Zlib / BZip2
    deps.set_property("zlib", "cmake_file_name", "ZLIB")
    deps.set_property("zlib", "cmake_target_name", "ZLIB::ZLIB")
    deps.set_property("bzip2", "cmake_file_name", "BZip2")
    deps.set_property("bzip2", "cmake_target_name", "BZip2::BZip2")

    # Cairo / Freetype
    deps.set_property("cairo", "cmake_file_name", "Cairo")
    deps.set_property("cairo", "cmake_target_name", "Cairo::Cairo")
    deps.set_property("freetype", "cmake_file_name", "Freetype")
    deps.set_property("freetype", "cmake_target_name", "Freetype::Freetype")

    deps.generate()

  def requirements(self):
    self.requires("boost/1.89.0")
    self.requires("zlib/1.3.1")
    self.requires("sqlite3/3.51.0")
    if self.options.with_cairo:
      self.requires("cairo/1.18.0")
    if self.options.with_eigen:
      self.requires("eigen/3.4.0")
    if self.options.with_python:
      self.requires("numpy/1.26.0")

  def build(self):
    cmake = CMake(self)
    cmake.configure()
    # cmake.build()
    # Build internal RDKit libraries first, sequentially to avoid race conditions on Windows

    cmake.build(cli_args=["--target", "install", "--", "/m:1"])
    # Create temporary build environment for RDKit tests
    # env = Environment()
    # env.define("RDBASE", self.source_folder)
    # env.define("RDBase", self.source_folder)
    # env.prepend_path("PATH", f"{self.build_folder}")  # where DLLs are
    # env.prepend_path("PATH", f"{self.build_folder}/bin/Release")
    #
    # # --- Include dependency run environment ---
    # run_env = VirtualRunEnv(self)
    # run_env.generate()
    #
    # envvars = env.vars(self)
    #
    # with envvars.apply():

    if self.options.with_ctest:
      run_env = VirtualRunEnv(self)
      env = run_env.environment()

      # Add RDKit-specific paths
      env.define("RDBASE", self.source_folder)
      env.define("RDBase", self.source_folder)
      env.prepend_path("PATH", f"{self.build_folder}")
      env.prepend_path("PATH", f"{self.build_folder}/bin/Release")

      with env.vars(self).apply():
        self.run(
          #f"ctest -C Release --output-on-failure -T Test",
          f"ctest -C Release --output-on-failure",
          cwd=self.build_folder,
        )

  def package(self):
    # Package is already installed in build() via cmake.install()
    cmake = CMake(self)
    cmake.install()

  def package_info(self):
    self.cpp_info.libs = ["RDKit"]
