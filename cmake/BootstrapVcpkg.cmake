# Fetch a normal, build-local checkout. No dependency is a Git submodule.
set(POB_DEPENDENCY_ROOT "${CMAKE_CURRENT_LIST_DIR}/../out/deps")
file(MAKE_DIRECTORY "${POB_DEPENDENCY_ROOT}")
# Keep the default package cache disposable along with the rest of the build.
# An explicitly configured shared cache remains supported.
if(NOT DEFINED ENV{VCPKG_DEFAULT_BINARY_CACHE} OR "$ENV{VCPKG_DEFAULT_BINARY_CACHE}" STREQUAL "")
    set(_pob_binary_cache "${CMAKE_CURRENT_LIST_DIR}/../out/cache/vcpkg")
    file(MAKE_DIRECTORY "${_pob_binary_cache}")
    set(ENV{VCPKG_DEFAULT_BINARY_CACHE} "${_pob_binary_cache}")
endif()

file(READ "${CMAKE_CURRENT_LIST_DIR}/sources.lock.json" _pob_source_lock)
string(JSON _pob_vcpkg_revision GET "${_pob_source_lock}" vcpkg revision)
string(JSON _pob_vcpkg_repository GET "${_pob_source_lock}" vcpkg repository)
find_program(POB_GIT_EXECUTABLE git REQUIRED)
set(POB_VCPKG_SOURCE_DIR "${POB_DEPENDENCY_ROOT}/vcpkg-src")
# Serialize bootstrap across Debug/Release configurations.
file(LOCK "${POB_DEPENDENCY_ROOT}/vcpkg-fetch.lock" GUARD FILE TIMEOUT 300)
if(NOT EXISTS "${POB_VCPKG_SOURCE_DIR}/.git")
    execute_process(COMMAND "${POB_GIT_EXECUTABLE}" init "${POB_VCPKG_SOURCE_DIR}"
        COMMAND_ERROR_IS_FATAL ANY)
endif()
execute_process(COMMAND "${POB_GIT_EXECUTABLE}" -C "${POB_VCPKG_SOURCE_DIR}"
    rev-parse HEAD OUTPUT_VARIABLE _pob_vcpkg_current OUTPUT_STRIP_TRAILING_WHITESPACE
    ERROR_QUIET)
if(NOT _pob_vcpkg_current STREQUAL _pob_vcpkg_revision)
    execute_process(COMMAND "${POB_GIT_EXECUTABLE}" -C "${POB_VCPKG_SOURCE_DIR}"
        fetch --depth 1 "${_pob_vcpkg_repository}" "${_pob_vcpkg_revision}"
        COMMAND_ERROR_IS_FATAL ANY)
    execute_process(COMMAND "${POB_GIT_EXECUTABLE}" -C "${POB_VCPKG_SOURCE_DIR}"
        checkout --detach "${_pob_vcpkg_revision}" COMMAND_ERROR_IS_FATAL ANY)
endif()
