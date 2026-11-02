# The ChemDraw wrapper calls expatpp directly, including in shared builds.
# Declare that dependency and install it even when the vendor directory uses
# EXCLUDE_FROM_ALL. Static builds already have an upstream install rule.
if(TARGET expat AND TARGET RDChemDrawLib)
  set_target_properties(expat PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${RDK_RUNTIME_OUTPUT_DIRECTORY}"
    LIBRARY_OUTPUT_DIRECTORY "${RDK_LIBRARY_OUTPUT_DIRECTORY}"
    ARCHIVE_OUTPUT_DIRECTORY "${RDK_ARCHIVE_OUTPUT_DIRECTORY}")
  foreach(target RDChemDrawLib RDChemDrawReactionLib)
    if(TARGET "${target}")
      target_link_libraries("${target}" PUBLIC expat)
    endif()
  endforeach()
  if(BUILD_SHARED_LIBS AND NOT RDK_INSTALL_STATIC_LIBS)
    install(TARGETS expat EXPORT rdkit-targets DESTINATION "${RDKit_LibDir}")
  endif()
endif()

include("${CMAKE_CURRENT_LIST_DIR}/package-metadata.cmake")
