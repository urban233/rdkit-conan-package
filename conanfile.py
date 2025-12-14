# ----------------------------------------------------------------------------#
# This file contains source code for the Conan RDKit package
# copyright (c) 2025 by Martin Urban.
# It is unlawful to modify or remove this copyright notice.
# Please see the accompanying LICENSE file for further information.
# ----------------------------------------------------------------------------#
import os
import pathlib
import shutil

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualRunEnv
from conan.tools.files import copy, get, replace_in_file


class RDKitConan(ConanFile):
  """Conan recipe for RDKit.

  RDKit is a collection of cheminformatics and machine-learning software
  written in C++ and Python. This recipe handles the complex build configuration
  required for RDKit, including various optional support libraries and
  platform-specific build flags.
  """

  name = "rdkit"
  version = "2025.09.3"
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
  }

  default_options = {
    "shared": False,
    "with_python": False,
    "with_inchi": True,
    "with_cairo": True,
    "with_eigen": True,
    # Conan specific options
    "with_ctest": False,
  }

  exports_sources = "CMakeLists.txt"

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
    shutil.copyfile(
      os.path.join(self.export_sources_folder, "CMakeLists.txt"),
      os.path.join(self.source_folder, "CMakeLists.txt")
    )

    replace_in_file(
      self,
      os.path.join(self.source_folder, "Code", "JavaWrappers", "CMakeLists.txt"),
      "include(${SWIG_USE_FILE})",
      "include(UseSWIG)"
    )
    # Fix Java SWIG unique_ptr<RWMol> compilation errors.
    # Only replace the first occurrence (unique_ptr block), not all SWIGCSHARP blocks.
    replace_in_file(
      self,
      os.path.join(self.source_folder, "Code", "JavaWrappers", "ROMol.i"),
      "#ifdef SWIGCSHARP\n%include <std_unique_ptr.i>",
      "#if defined(SWIGCSHARP) || defined(SWIGJAVA)\n%include <std_unique_ptr.i>"
    )
    # # Fix Windows linker errors for unexported Hybridizations class.
    # replace_in_file(
    #   self,
    #   os.path.join(self.source_folder, "Code", "JavaWrappers", "MolOps.i"),
    #   "%ignore RDKit::MolOps::detectChemistryProblems;",
    #   "%ignore RDKit::MolOps::detectChemistryProblems;\n%ignore RDKit::MolOps::Hybridizations;"
    # )
    # # Fix Windows linker error for unexported calculateImplicitValence friend function.
    # # Must be placed before %include <GraphMol/Atom.h> in Atom.i
    # replace_in_file(
    #   self,
    #   os.path.join(self.source_folder, "Code", "JavaWrappers", "Atom.i"),
    #   "%ignore RDKit::Atom::Match(const Atom *) const;",
    #   "%ignore RDKit::Atom::Match(const Atom *) const;\n%ignore RDKit::calculateImplicitValence;"
    # )

  def layout(self):
    """Defines the standard CMake layout for the project."""
    cmake_layout(
      self,
      src_folder="src",
      build_folder="src/build"
    )

  def configure(self):
    """Configures build options and dependency flags."""
    if self.options.shared:
      self.options.rm_safe("fPIC")

    # Propagate options to Boost to ensure binary compatibility.
    # RDKit typically requires specific Boost components to be present
    # and linked dynamically.
    # self.options["boost"].shared = True
    self.options["boost"].shared = True
    self.options["boost"].without_iostreams = False
    self.options["boost"].without_zlib = False
    self.options["boost"].without_serialization = False  # Required by RDKit
    self.options["boost"].without_system = False

  def generate(self):
    """Generates the build toolchains and dependency files."""
    # --- CMake Toolchain Configuration ---
    tc = CMakeToolchain(self)

    # Configuration mirrors the official Azure Pipelines build definition
    tc.variables["CMAKE_BUILD_TYPE"] = "Release"
    tc.variables["RDK_INSTALL_INTREE"] = "OFF"  # Enforce use of package folder
    # tc.variables["RDK_INSTALL_INTREE"] = "ON"  # Enforce use of package folder

    # Normalize path separators to ensure CMake handles the install prefix correctly
    if self.package_folder:
      tc.variables["CMAKE_INSTALL_PREFIX"] = self.package_folder.replace("\\", "/")

    # Set the SWIG executable from the Conan package (tool_requires are in build context)
    swig_dep = self.dependencies.build.get("swig")
    if swig_dep:
      swig_exe = os.path.join(swig_dep.package_folder, "bin", "swig.exe" if self.settings.os == "Windows" else "swig")
      tc.cache_variables["SWIG_EXECUTABLE"] = swig_exe.replace("\\", "/")

    # RDKit Build Flags
    # tc.variables["RDK_INSTALL_STATIC_LIBS"] = "OFF"
    tc.variables["RDK_INSTALL_STATIC_LIBS"] = "ON"
    # tc.variables["RDK_INSTALL_DLLS_MSVC"] = "ON"
    tc.variables["RDK_INSTALL_DLLS_MSVC"] = "OFF"

    if self.options.with_ctest:
      tc.variables["RDK_BUILD_CPP_TESTS"] = "ON"
    else:
      tc.variables["RDK_BUILD_CPP_TESTS"] = "OFF"

    tc.variables["RDK_BUILD_PYTHON_WRAPPERS"] = "OFF"
    tc.variables["RDK_BUILD_COORDGEN_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_MAEPARSER_SUPPORT"] = "ON"
    tc.variables["RDK_OPTIMIZE_POPCNT"] = "ON"
    # tc.variables["RDK_BUILD_TEST_GZIP"] = "ON"
    tc.variables["RDK_BUILD_TEST_GZIP"] = "OFF"
    tc.variables["RDK_BUILD_FREESASA_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_AVALON_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_INCHI_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_YAEHMOP_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_XYZ2MOL_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_CAIRO_SUPPORT"] = "ON"
    tc.variables["RDK_BUILD_THREADSAFE_SSS"] = "ON"
    # tc.variables["RDK_BUILD_SWIG_WRAPPERS"] = "ON"
    tc.variables["RDK_BUILD_SWIG_WRAPPERS"] = "OFF"
    # tc.variables["RDK_BUILD_SWIG_JAVA_WRAPPER"] = "ON"
    tc.variables["RDK_BUILD_SWIG_JAVA_WRAPPER"] = "OFF"
    tc.variables["RDK_BUILD_SWIG_CSHARP_WRAPPER"] = "OFF"
    # tc.variables["RDK_SWIG_STATIC"] = "ON"
    tc.variables["RDK_SWIG_STATIC"] = "OFF"
    tc.variables["RDK_TEST_MULTITHREADED"] = "ON"

    # 1. Remove MSVC runtime enforcement to allow usage of the default VS runtime.
    if "CMAKE_MSVC_RUNTIME_LIBRARY" in tc.cache_variables:
      del tc.cache_variables["CMAKE_MSVC_RUNTIME_LIBRARY"]

    # 2. Remove parallel compilation flags (/MP) automatically added by Conan.
    tc.cache_variables.pop("CONAN_CXX_FLAGS", None)
    tc.cache_variables.pop("CONAN_C_FLAGS", None)

    tc.generate()

    # --- CMake Dependency Configuration ---
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
    # Configure SWIG
    deps.set_property("swig", "cmake_file_name", "SWIG")
    deps.set_property("swig", "cmake_target_name", "SWIG::SWIG")

    deps.generate()

  def requirements(self):
    """Defines the package dependencies."""
    # Special override which is necessary because cairo and swig need this
    # but in different minors cairo .42 and swig .43
    self.requires("pcre2/10.43", override=True)
    # --------------------------------------------------------------------------
    self.requires("boost/1.89.0")
    self.requires("zlib/1.3.1")
    self.requires("sqlite3/3.51.0")


    if self.options.with_cairo:
      self.requires("cairo/1.18.0")
    if self.options.with_eigen:
      self.requires("eigen/3.4.0")
    if self.options.with_python:
      self.requires("numpy/1.26.0")

  def build_requirements(self):
    """Builds the required packages."""
    self.tool_requires("swig/4.4.0")

  def build(self):
    """Builds the project using CMake."""
    cmake = CMake(self)
    cmake.configure()

    # Build internal RDKit libraries sequentially.
    # This is critical on Windows to avoid race conditions during the build process.
    # We target 'install' directly with single-process execution (/m:1).
    # cmake.build(cli_args=["--target", "install", "--", "/m:1"])
    cmake.build(cli_args=["--target", "install"])

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
    env.prepend_path("PATH", f"{self.build_folder}/bin/Release")

    with env.vars(self).apply():
      self.run(
        "ctest -C Release --output-on-failure",
        cwd=self.build_folder,
      )

  def package(self):
    """Packages the artifacts, reorganizing headers and binaries."""
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

  def package_info(self):
    """Defines the package information for consumers."""
    self.cpp_info.set_property("cmake_file_name", "RDKit")

    # List of RDKit component libraries.
    # Note: Some libraries (ConformerParser, rdkit_base, rdkit_py_base, yaehmop_eht)
    # are missing from the manifest.
    libs = [
      "Abbreviations",
      "Alignment",
      "AvalonLib",
      "avalon_clib",
      "Catalogs",
      "ChemDraw",
      "ChemicalFeatures",
      "ChemReactions",
      "ChemTransforms",
      "CIPLabeler",
      "coordgen",
      "DataStructs",
      "Depictor",
      "Deprotect",
      "Descriptors",
      "DetermineBonds",
      "DistGeometry",
      "DistGeomHelpers",
      "EHTLib",
      "EigenSolvers",
      "EnumerateStereoisomers",
      "FileParsers",
      "FilterCatalog",
      "Fingerprints",
      "FMCS",
      "ForceField",
      "ForceFieldHelpers",
      "FragCatalog",
      "FreeSASALib",
      "freesasa_clib",
      "ga",
      "GeneralizedSubstruct",
      "GenericGroups",
      "GraphMol",
      "hc",
      "Inchi",
      "InfoTheory",
      "maeparser",
      "MarvinParser",
      "MMPA",
      "MolAlign",
      "MolCatalog",
      "MolChemicalFeatures",
      "MolDraw2D",
      "MolEnumerator",
      "MolHash",
      "MolInteractionFields",
      "MolInterchange",
      "MolProcessing",
      "MolStandardize",
      "MolTransforms",
      "O3AAlign",
      "Optimizer",
      "PartialCharges",
      "PubChemShape",
      "pubchem_align3d",
      "RascalMCES",
      "RDChemDrawLib",
      "RDChemDrawReactionLib",
      "RDGeneral",
      "RDGeometryLib",
      "RDInchiLib",
      "RDStreams",
      "ReducedGraphs",
      "RGroupDecomposition",
      "RingDecomposerLib",
      "ScaffoldNetwork",
      "ShapeHelpers",
      "SimDivPickers",
      "SLNParse",
      "SmilesParse",
      "Subgraphs",
      "SubstructLibrary",
      "SubstructMatch",
      "SynthonSpaceSearch",
      "TautomerQuery",
      "Trajectory"
    ]

    deps = [
      "boost::boost",
      "zlib::zlib",
      "sqlite3::sqlite3",
    ]

    if self.options.with_cairo:
      deps.append("cairo::cairo")
    if self.options.with_eigen:
      deps.append("eigen::eigen")
    if self.options.with_python:
      deps.append("numpy::numpy")

    # Create a CMake component for each RDKit sub-library.
    for name in libs:
      comp = self.cpp_info.components[name]
      # comp.libs = [f"RDKit{name}"]  # If shared
      comp.libs = [name]  # if static
      comp.set_property("cmake_target_name", f"RDKit::{name}")
      # Each RDKit component depends on the common external packages.
      comp.requires = deps.copy()
