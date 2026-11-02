add_executable(pob-linux "${PROJECT_SOURCE_DIR}/source/native/launcher/main.cpp")
target_link_libraries(pob-linux PRIVATE SimpleGraphic pob-compiler-options)
set_target_properties(pob-linux SimpleGraphic lcurl lzip lua-utf8 luasocket PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin"
    BUILD_RPATH "$ORIGIN")
# Lua require() expects these filenames, with no Unix library prefix.
set_target_properties(lcurl lzip lua-utf8 luasocket PROPERTIES PREFIX "")
# Lua's hierarchical module lookup also accepts socket/core.so directly.
set_target_properties(luasocket PROPERTIES
    BUILD_RPATH "$ORIGIN/.."
    OUTPUT_NAME "core"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin/socket")
add_custom_target(stage
    COMMAND "${CMAKE_COMMAND}" -E copy_directory
        "${PROJECT_SOURCE_DIR}/source/resources/fonts" "${CMAKE_BINARY_DIR}/bin/SimpleGraphic/Fonts"
    COMMAND "${CMAKE_COMMAND}" -E copy_directory
        "${PROJECT_SOURCE_DIR}/source/resources/lua" "${CMAKE_BINARY_DIR}/bin/lua"
    COMMAND "${CMAKE_COMMAND}" -E copy_directory
        "${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}/share/luajit-2.1/jit"
        "${CMAKE_BINARY_DIR}/bin/lua/jit"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${CMAKE_BINARY_DIR}/bin/resources"
    COMMAND "${CMAKE_COMMAND}" -E copy_if_different
        "${PROJECT_SOURCE_DIR}/source/resources/manifest.xml"
        "${PROJECT_SOURCE_DIR}/source/resources/help.txt"
        "${PROJECT_SOURCE_DIR}/source/resources/changelog.txt"
        "${CMAKE_BINARY_DIR}/bin/resources"
    COMMAND "${CMAKE_COMMAND}" -E create_symlink
        "${PROJECT_SOURCE_DIR}/source/lua" "${CMAKE_BINARY_DIR}/bin/src"
    COMMAND "${CMAKE_COMMAND}"
        "-DPOB_BIN_DIR=${CMAKE_BINARY_DIR}/bin"
        "-DPOB_VCPKG_PREFIX=${VCPKG_INSTALLED_DIR}/${VCPKG_TARGET_TRIPLET}"
        -P "${PROJECT_SOURCE_DIR}/cmake/StageLibraries.cmake"
    DEPENDS pob-linux lcurl lzip lua-utf8 luasocket
    COMMENT "Stage Linux runtime, fonts, Lua modules and application source link")
