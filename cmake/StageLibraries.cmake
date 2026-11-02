# Collect the privately built shared-library closure, retaining system libc,
# libstdc++ and graphics drivers as host dependencies.
file(GET_RUNTIME_DEPENDENCIES
    EXECUTABLES "${POB_BIN_DIR}/pob-linux"
    LIBRARIES "${POB_BIN_DIR}/lcurl.so" "${POB_BIN_DIR}/lzip.so"
        "${POB_BIN_DIR}/lua-utf8.so" "${POB_BIN_DIR}/socket/core.so"
    RESOLVED_DEPENDENCIES_VAR _pob_resolved
    UNRESOLVED_DEPENDENCIES_VAR _pob_unresolved)
if(_pob_unresolved)
    message(FATAL_ERROR "Unresolved runtime libraries: ${_pob_unresolved}")
endif()
foreach(_pob_library IN LISTS _pob_resolved)
    cmake_path(IS_PREFIX POB_VCPKG_PREFIX "${_pob_library}" NORMALIZE _pob_private)
    if(_pob_private)
        file(COPY "${_pob_library}" DESTINATION "${POB_BIN_DIR}" FOLLOW_SYMLINK_CHAIN)
    endif()
endforeach()
