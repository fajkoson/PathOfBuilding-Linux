include(FetchContent)
file(READ "${CMAKE_CURRENT_LIST_DIR}/sources.lock.json" _pob_source_lock)
set(FETCHCONTENT_BASE_DIR "${POB_DEPENDENCY_ROOT}" CACHE PATH "Fetched dependency sources" FORCE)
foreach(_pob_name IN ITEMS imgui compressonator lcurl luautf8 luasocket)
    string(JSON _pob_url GET "${_pob_source_lock}" "${_pob_name}" url)
    string(JSON _pob_sha256 GET "${_pob_source_lock}" "${_pob_name}" sha256)
    set(_pob_patch_args)
    set(_pob_patch "${CMAKE_CURRENT_LIST_DIR}/patches/${_pob_name}.patch")
    if(EXISTS "${_pob_patch}")
        file(SHA256 "${_pob_patch}" _pob_patch_sha256)
        set(_pob_patch_args PATCH_COMMAND "${CMAKE_COMMAND}"
            "-DPOB_SOURCE=<SOURCE_DIR>" "-DPOB_PATCH=${_pob_patch}"
            "-DPOB_PATCH_SHA256=${_pob_patch_sha256}"
            -P "${CMAKE_CURRENT_LIST_DIR}/ApplyDependencyPatch.cmake")
    endif()
    FetchContent_Declare(${_pob_name}
        ${_pob_patch_args}
        URL "${_pob_url}"
        URL_HASH "SHA256=${_pob_sha256}"
        DOWNLOAD_EXTRACT_TIMESTAMP FALSE
        # Sources are compiled by SimpleGraphic, not their standalone projects.
        SOURCE_SUBDIR __pob_download_only__)
    FetchContent_MakeAvailable(${_pob_name})
    set(POB_${_pob_name}_SOURCE_DIR "${${_pob_name}_SOURCE_DIR}")
endforeach()
