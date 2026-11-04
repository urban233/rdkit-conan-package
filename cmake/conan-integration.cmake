if(TARGET rdkitCatch)
  target_link_libraries(rdkitCatch PUBLIC RDGeneral)
endif()

# rdkit_library() refers to a *_static variant for internal static dependencies.
if(TARGET yaehmop_eht AND NOT TARGET yaehmop_eht_static)
  add_library(yaehmop_eht_static ALIAS yaehmop_eht)
endif()

# ChemDraw's C++ helper now uses the Conan-provided Expat library.
# Propagate its public headers and install the helper in shared packages too.
if(TARGET expatpp)
  target_link_libraries(expatpp PUBLIC EXPAT::EXPAT)
  set_target_properties(expatpp PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${RDK_RUNTIME_OUTPUT_DIRECTORY}"
    LIBRARY_OUTPUT_DIRECTORY "${RDK_LIBRARY_OUTPUT_DIRECTORY}"
    ARCHIVE_OUTPUT_DIRECTORY "${RDK_ARCHIVE_OUTPUT_DIRECTORY}")
  foreach(target ChemDraw ChemDraw_static
                 RDChemDrawLib RDChemDrawLib_static
                 RDChemDrawReactionLib RDChemDrawReactionLib_static)
    if(TARGET "${target}")
      target_link_libraries("${target}" PUBLIC expatpp EXPAT::EXPAT)
    endif()
  endforeach()
  if(BUILD_SHARED_LIBS AND NOT RDK_INSTALL_STATIC_LIBS)
    install(TARGETS expatpp EXPORT rdkit-targets DESTINATION "${RDKit_LibDir}")
  endif()
endif()

include("${CMAKE_CURRENT_LIST_DIR}/package-metadata.cmake")
