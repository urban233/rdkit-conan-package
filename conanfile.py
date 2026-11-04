# ---------------------------------------------------------------------------- #
# This file contains source code for the Conan RDKit package
# copyright (c) 2025 by Martin Urban.
# It is unlawful to modify or remove this copyright notice.
# Please see the accompanying LICENSE file for further information.
# ---------------------------------------------------------------------------- #
import json
import os
import shutil
from io import StringIO

from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import collect_libs, copy, get, load, replace_in_file, save


class RDKitConan(ConanFile):
  """Conan recipe for RDKit.

  RDKit is a collection of cheminformatics and machine-learning software
  written in C++ and Python. This recipe handles the complex build configuration
  required for RDKit, including various optional support libraries and
  platform-specific build flags.
  """

  name = "rdkit"
  version = "2026.09.1"
  license = "BSD-3-Clause"
  url = "https://github.com/rdkit/rdkit"
  description = (
    "The RDKit is a collection of cheminformatics and machine-learning "
    "software written in C++ and Python."
  )
  topics = ("chemistry", "cheminformatics", "c++", "python", "molecule")

  settings = "os", "compiler", "build_type", "arch"

  options = {
    "shared": [True, False],
    "with_python": [True, False],
    "with_inchi": [True, False],
    "with_cairo": [True, False],
    "with_eigen": [True, False],
    # Conan specific options
    "with_ctest": [True, False],
    "with_java": [True, False],
    "with_csharp": [True, False],
  }

  default_options = {
    "shared": False,
    "with_python": False,
    "with_inchi": True,
    "with_cairo": True,
    "with_eigen": True,
    # Conan specific options
    "with_ctest": True,
    "with_java": False,
    "with_csharp": False
  }

  exports_sources = "cmake/*"

  def validate(self):
    check_min_cppstd(self, "20")

  def source(self):
    """Retrieves and prepares the source code."""
    # Download source code based on the version tag.
    get(
      self,
      url=(
        f"https://github.com/rdkit/rdkit/archive/refs/tags/"
        f"Release_{self.version.replace('.', '_')}.zip"
      ),
      strip_root=True
    )

    # Overwrite the root CMakeLists.txt with the exported version.
    # TODO: Consider replacing this file replacement strategy with a patch file
    # for more robust source management.
    # shutil.copyfile(
    #   os.path.join(self.export_sources_folder, "CMakeLists.txt"),
    #   os.path.join(self.source_folder, "CMakeLists.txt")
    # )

    # Adding the set(Boost_USE_STATIC_LIBS ON) but only if
    # RDK_INSTALL_DLLS_MSVC=OFF
    replace_in_file(
      self,
      os.path.join(self.source_folder, "CMakeLists.txt"),
      "# FIX: do we still need this?",
      "# FIX: do we still need this?\nif(NOT RDK_INSTALL_DLLS_MSVC)\n  set(Boost_USE_STATIC_LIBS ON)\nendif()"
    )

    # Fix the Eigen3 discovery to make it conan compatible
    replace_in_file(
      self,
      os.path.join(self.source_folder, "CMakeLists.txt"),
      "find_package(Eigen3 NO_MODULE)",
      "find_package(Eigen3 REQUIRED CONFIG)\nfind_package(EXPAT REQUIRED CONFIG)"
    )

    # Replace the ${SWIG_USE_FILE} variable for UseSWIG to make it conan compatible
    replace_in_file(
      self,
      os.path.join(self.source_folder, "Code", "JavaWrappers", "CMakeLists.txt"),
      "include(${SWIG_USE_FILE})",
      "include(UseSWIG)"
    )
    # The additional ChemDraw link must follow the same static/shared selection
    # as the other SWIG libraries, instead of retaining a build-tree dependency.
    replace_in_file(
      self,
      os.path.join(self.source_folder, "Code", "JavaWrappers", "gmwrapper", "CMakeLists.txt"),
      "rdkit_base ${RDKit_THREAD_LIBS} ChemDraw expatpp EXPAT::EXPAT)",
      "rdkit_base ${RDKit_THREAD_LIBS} ChemDraw${swigRDKitLibSuffix} expatpp EXPAT::EXPAT)"
    )

    # Test entry points and the private EHT implementation are static helpers,
    # even when the public RDKit libraries are shared.
    replace_in_file(
      self, os.path.join(self.source_folder, "Code", "RDGeneral", "CMakeLists.txt"),
      "add_library(rdkitCatch catch_main.cpp)",
      "add_library(rdkitCatch STATIC catch_main.cpp)"
    )
    replace_in_file(
      self, os.path.join(self.source_folder, "CMakeLists.txt"),
      "FetchContent_MakeAvailable(Catch2)",
      'set(_saved_shared_before_catch "${BUILD_SHARED_LIBS}")\n'
      'set(BUILD_SHARED_LIBS OFF)\n'
      'FetchContent_MakeAvailable(Catch2)\n'
      'set(BUILD_SHARED_LIBS "${_saved_shared_before_catch}")'
    )
    # RDKit's sharded tests include CatchShardTests before adding Code/.
    # Expose the extras from either the fetched or installed Catch2 package.
    replace_in_file(
      self, os.path.join(self.source_folder, "CMakeLists.txt"),
      "include(RDKitUtils)",
      'if(DEFINED catch2_SOURCE_DIR)\n'
      '  list(APPEND CMAKE_MODULE_PATH "${catch2_SOURCE_DIR}/extras")\n'
      'elseif(DEFINED Catch2_DIR)\n'
      '  list(APPEND CMAKE_MODULE_PATH "${Catch2_DIR}")\n'
      'endif()\n'
      'include(RDKitUtils)'
    )
    replace_in_file(
      self, os.path.join(self.source_folder, "External", "YAeHMOP", "CMakeLists.txt"),
      "add_subdirectory(yaehmop/tightbind EXCLUDE_FROM_ALL True)",
      'set(_saved_build_shared_libs "${BUILD_SHARED_LIBS}")\n'
      'set(BUILD_SHARED_LIBS OFF)\n'
      'add_subdirectory(yaehmop/tightbind EXCLUDE_FROM_ALL True)\n'
      'set(BUILD_SHARED_LIBS "${_saved_build_shared_libs}")'
    )
    # Random-access suppliers require byte offsets; Windows text-mode streams
    # translate line endings and invalidate the test's seek/tell positions.
    replace_in_file(
      self, os.path.join(self.source_folder, "Code", "GraphMol", "FileParsers", "v2_suppliers_catch.cpp"),
      "std::ifstream inStream(fName);",
      "std::ifstream inStream(fName, std::ios_base::binary);"
    )

    copy(self, "*.cmake", src=os.path.join(self.export_sources_folder, "cmake"),
         dst=os.path.join(self.source_folder, "conan-cmake"))
    root_cmake = os.path.join(self.source_folder, "CMakeLists.txt")
    save(self, root_cmake, load(self, root_cmake) +
         '\ninclude("${CMAKE_CURRENT_SOURCE_DIR}/conan-cmake/conan-integration.cmake")\n')

  def layout(self):
    """Defines the standard CMake layout for the project."""
    cmake_layout(
      self,
      src_folder="src",
      build_folder="src/build"
    )

  def configure(self):
    """Configures build options and dependency flags."""
    if self.options.with_python or self.options.with_csharp:
      raise ConanInvalidConfiguration("Python and C# bindings are not supported by this recipe")
    if not self.options.with_eigen:
      raise ConanInvalidConfiguration("This recipe requires with_eigen=True")
    if self.options.shared:
      self.options.rm_safe("fPIC")

    # Propagate options to Boost to ensure binary compatibility.
    # RDKit typically requires specific Boost components to be present
    # and linked dynamically.
    self.options["boost"].shared = self.options.shared
    self.options["boost"].without_iostreams = False
    self.options["boost"].without_zlib = False
    self.options["boost"].without_serialization = False  # Required by RDKit
    self.options["boost"].without_system = False

  def generate(self):
    """Generates the build toolchains and dependency files."""
    # <editor-fold desc="CMake Toolchain Configuration">
    tc = CMakeToolchain(self)

    tc.variables["CMAKE_BUILD_TYPE"] = str(self.settings.build_type)
    tc.variables["EXECUTABLE_OUTPUT_PATH"] = os.path.join(self.build_folder, "bin").replace("\\", "/")
    # TBB is only used by upstream test executables, never by the package.
    tc.variables["CMAKE_DISABLE_FIND_PACKAGE_TBB"] = not bool(self.options.with_ctest)

    # Normalize path separators to ensure CMake handles the install prefix correctly
    if self.package_folder:
      tc.variables["CMAKE_INSTALL_PREFIX"] = self.package_folder.replace("\\", "/")

    # <editor-fold desc="RDKit Build Flags">
    tc.variables["RDK_INSTALL_INTREE"] = "OFF"  # Enforce use of package folder

    # <editor-fold desc="Shared vs. static">
    if self.options.shared:
      tc.variables["RDK_INSTALL_STATIC_LIBS"] = "OFF"
      tc.variables["RDK_INSTALL_DLLS_MSVC"] = "ON"
    else:
      tc.variables["RDK_INSTALL_STATIC_LIBS"] = "ON"
      tc.variables["RDK_INSTALL_DLLS_MSVC"] = "OFF"
    # </editor-fold>

    # <editor-fold desc="CTest related">
    if self.options.with_ctest:
      tc.variables["RDK_BUILD_CPP_TESTS"] = "ON"
    else:
      tc.variables["RDK_BUILD_CPP_TESTS"] = "OFF"
    # </editor-fold>

    # <editor-fold desc="Library support related">
    # Python support is not yet supported
    tc.variables["RDK_BUILD_PYTHON_WRAPPERS"] = "OFF"
    tc.variables["RDK_BUILD_COORDGEN_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_MAEPARSER_SUPPORT"] = "ON"
    tc.variables["RDK_OPTIMIZE_POPCNT"] = "ON"
    tc.variables["RDK_BUILD_TEST_GZIP"] = "OFF"
    tc.variables["RDK_BUILD_FREESASA_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_AVALON_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_INCHI_SUPPORT"] = bool(self.options.with_inchi)
    tc.variables["RDK_BUILD_YAEHMOP_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_XYZ2MOL_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_CAIRO_SUPPORT"] = bool(self.options.with_cairo)
    tc.variables["RDK_BUILD_THREADSAFE_SSS"] = "ON"
    # </editor-fold>

    # <editor-fold desc="SWIG related">
    if self.options.with_java or self.options.with_csharp:
      tc.variables["RDK_BUILD_SWIG_WRAPPERS"] = "ON"
      tc.variables["RDK_SWIG_STATIC"] = "ON"
      # Set the SWIG executable from the Conan package
      swig_dep = self.dependencies.build.get("swig")
      swig_exe = os.path.join(swig_dep.package_folder, "bin", "swig.exe" if self.settings.os == "Windows" else "swig")
      tc.cache_variables["SWIG_EXECUTABLE"] = swig_exe.replace("\\", "/")
    else:
      tc.variables["RDK_BUILD_SWIG_WRAPPERS"] = "OFF"
      tc.variables["RDK_SWIG_STATIC"] = "OFF"

    if self.options.with_java:
      tc.variables["RDK_BUILD_SWIG_JAVA_WRAPPER"] = "ON"
    else:
      tc.variables["RDK_BUILD_SWIG_JAVA_WRAPPER"] = "OFF"

    if self.options.with_csharp:
      tc.variables["RDK_BUILD_SWIG_CSHARP_WRAPPER"] = "ON"
    else:
      tc.variables["RDK_BUILD_SWIG_CSHARP_WRAPPER"] = "OFF"
    # </editor-fold>

    tc.variables["RDK_TEST_MULTITHREADED"] = "ON"
    # </editor-fold>

    # Remove MSVC runtime enforcement to allow usage of the default VS runtime.
    if "CMAKE_MSVC_RUNTIME_LIBRARY" in tc.cache_variables:
      del tc.cache_variables["CMAKE_MSVC_RUNTIME_LIBRARY"]

    # Remove parallel compilation flags (/MP) automatically added by Conan.
    tc.cache_variables.pop("CONAN_CXX_FLAGS", None)
    tc.cache_variables.pop("CONAN_C_FLAGS", None)

    tc.generate()
    # </editor-fold>

    # <editor-fold desc="CMake Dependency Configuration">
    deps = CMakeDeps(self)

    # Configure Eigen
    deps.set_property("eigen", "cmake_file_name", "Eigen3")
    deps.set_property("eigen", "cmake_target_name", "Eigen3::Eigen")
    tc.cache_variables["EIGEN3_FOUND"] = True

    # Configure Zlib / BZip2
    deps.set_property("zlib", "cmake_file_name", "ZLIB")
    deps.set_property("zlib", "cmake_target_name", "ZLIB::ZLIB")
    deps.set_property("bzip2", "cmake_file_name", "BZip2")
    deps.set_property("bzip2", "cmake_target_name", "BZip2::BZip2")

    # Configure Cairo / Freetype
    deps.set_property("cairo", "cmake_file_name", "Cairo")
    deps.set_property("cairo", "cmake_target_name", "Cairo::Cairo")
    deps.set_property("freetype", "cmake_file_name", "Freetype")
    deps.set_property("freetype", "cmake_target_name", "Freetype::Freetype")
    deps.set_property("expat", "cmake_file_name", "EXPAT")
    deps.set_property("expat", "cmake_target_name", "EXPAT::EXPAT")
    # Configure SWIG
    deps.set_property("swig", "cmake_file_name", "SWIG")
    deps.set_property("swig", "cmake_target_name", "SWIG::SWIG")

    deps.generate()
    # </editor-fold>

  def requirements(self):
    """Defines the package dependencies."""
    # Align Cairo and SWIG with the PCRE2 minor used by the SWIG binaries.
    self.requires("pcre2/10.44", override=True)
    # --------------------------------------------------------------------------
    self.requires("boost/1.89.0", transitive_headers=True)
    self.requires("zlib/1.3.1")
    self.requires("sqlite3/3.51.0")
    self.requires("freetype/2.15.0", transitive_headers=True)
    self.requires("expat/2.9.0", transitive_headers=True)

    if self.options.with_cairo:
      self.requires("cairo/1.18.0", transitive_headers=True)
    if self.options.with_eigen:
      self.requires("eigen/3.4.0", transitive_headers=True)
    if self.options.with_python:
      self.requires("numpy/1.26.0")

  def build_requirements(self):
    """Builds the required packages."""
    if self.options.with_ctest:
      tbb_options = {} if self.settings.os == "Macos" else {"tbbbind": False}
      self.test_requires("onetbb/2023.1.0", options=tbb_options)
    if self.options.with_java or self.options.with_csharp:
      self.tool_requires("swig/4.4.0")

  def build(self):
    """Builds the project using CMake."""
    cmake = CMake(self)
    cmake.configure()
    cmake.build()

    if self.options.with_ctest:
      self._run_tests()

  def _run_tests(self):
    """Executes the test suite using CTest."""
    run_env = VirtualRunEnv(self)
    env = run_env.environment()

    # Define RDKit-specific environment variables for the test runner.
    env.define("RDBASE", self.source_folder)
    env.define("RDBase", self.source_folder)
    env.prepend_path("PATH", f"{self.build_folder}")
    env.prepend_path("PATH", f"{self.build_folder}/bin")
    env.prepend_path("PATH", f"{self.build_folder}/bin/Release")
    env.prepend_path("LD_LIBRARY_PATH", os.path.join(self.build_folder, "lib"))
    env.prepend_path("DYLD_LIBRARY_PATH", os.path.join(self.build_folder, "lib"))

    with env.vars(self).apply():
      inventory = StringIO()
      self.run(f"ctest -C {self.settings.build_type} --show-only=json-v1",
               cwd=self.build_folder, stdout=inventory, env=None)
      save(self, os.path.join(self.build_folder, "upstream-inventory.json"), inventory.getvalue())
      self.run(
        f"ctest -C {self.settings.build_type} --output-on-failure --no-tests=error "
        "--output-junit upstream-tests.xml --timeout 600",
        cwd=self.build_folder,
        env=None,
      )

  def package(self):
    """Packages the artifacts, reorganizing headers and binaries."""
    CMake(self).install()
    include_src = os.path.join(self.package_folder, "include", "rdkit")
    include_dst = os.path.join(self.package_folder, "include")
    os.makedirs(include_dst, exist_ok=True)

    # Consolidate headers: Move all files from include/rdkit/ to include/
    for item in os.listdir(include_src):
      src_path = os.path.join(include_src, item)
      dst_path = os.path.join(include_dst, item)
      if os.path.isdir(src_path):
        shutil.move(src_path, dst_path)
      else:
        shutil.move(src_path, include_dst)

    if os.path.exists(include_src):
      os.rmdir(include_src)

    # Move DLLs from lib/ to bin/ for Windows runtime compatibility.
    lib_dir = os.path.join(self.package_folder, "lib")
    bin_dir = os.path.join(self.package_folder, "bin")
    os.makedirs(bin_dir, exist_ok=True)

    copy(self, "*.dll", src=lib_dir, dst=bin_dir, keep_path=False)
    copy(self, "license.txt", src=self.source_folder,
         dst=os.path.join(self.package_folder, "licenses"))
    copy(self, "rdkit-components.json", src=self.build_folder,
         dst=os.path.join(self.package_folder, "res"))

    if self.options.with_java:
      wrapper_source = os.path.join(self.source_folder, "Code", "JavaWrappers", "gmwrapper")
      copy(self, "org.RDKit.jar", src=wrapper_source,
           dst=os.path.join(self.package_folder, "share", "java"))
      wrapper_build = os.path.join(self.build_folder, "Code", "JavaWrappers", "gmwrapper")
      for pattern in ("*GraphMolWrap.dll", "*GraphMolWrap.so", "*GraphMolWrap.jnilib", "*GraphMolWrap.dylib"):
        copy(self, pattern, src=wrapper_build, dst=bin_dir, keep_path=False)

  def package_info(self):
    """Defines the package information for consumers."""
    self.cpp_info.set_property("cmake_file_name", "RDKit")

    metadata = json.loads(load(self, os.path.join(self.package_folder, "res", "rdkit-components.json")))
    installed = set(collect_libs(self))
    # Non-Windows RDKit builds install separate *_static targets alongside shared ones.
    use_static_suffix = not self.options.shared and self.settings.os != "Windows"
    selected = {}
    for target, entry in metadata.items():
      if entry["library"] not in installed:
        continue
      # EHTLib embeds this private helper when the public libraries are shared.
      if self.options.shared and target == "yaehmop_eht":
        continue
      is_static_variant = target.endswith("_static")
      if is_static_variant != use_static_suffix and target.removesuffix("_static") + "_static" in metadata:
        continue
      selected[target] = entry
    if not selected:
      raise ConanInvalidConfiguration("No installed RDKit libraries found")

    external = ["boost::boost", "zlib::zlib", "sqlite3::sqlite3", "freetype::freetype", "expat::expat"]
    if self.options.with_cairo:
      external.append("cairo::cairo")
    if self.options.with_eigen:
      external.append("eigen::eigen")
    for target, entry in selected.items():
      name = target.removesuffix("_static")
      component = self.cpp_info.components[name]
      component.libs = [entry["library"]]
      component.defines.extend(metadata["rdkit_base"]["defines"])
      component.set_property("cmake_target_name", f"RDKit::{name}")
      component.requires = external + [dependency.removesuffix("_static")
                                      for dependency in entry["requires"] if dependency in selected]
      if self.options.shared:
        component.defines.append("RDKIT_DYN_LINK")
      if self.settings.os == "Linux":
        component.system_libs = ["pthread", "dl", "m"]
    self.runenv_info.define_path("RDBASE", os.path.join(self.package_folder, "share", "RDKit"))
    self.runenv_info.define_path("RDBase", os.path.join(self.package_folder, "share", "RDKit"))
