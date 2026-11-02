add_executable(pob-native-tests runtime_tests.cpp)
target_include_directories(pob-native-tests PRIVATE
    "${PROJECT_SOURCE_DIR}/source/native/simplegraphic/engine")
target_link_libraries(pob-native-tests PRIVATE SimpleGraphic pob-compiler-options)
set_target_properties(pob-native-tests PROPERTIES BUILD_RPATH "$ORIGIN")
add_test(NAME native-file-search COMMAND pob-native-tests file-search)
add_test(NAME native-user-paths COMMAND pob-native-tests user-paths)
set_tests_properties(native-file-search native-user-paths PROPERTIES
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}" TIMEOUT 15)
