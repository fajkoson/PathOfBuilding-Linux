set(_pob_diagnostics_default OFF)
if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    set(_pob_diagnostics_default ON)
endif()
option(POB_RUNTIME_DIAGNOSTICS "Print native startup diagnostics to the terminal"
    ${_pob_diagnostics_default})
unset(_pob_diagnostics_default)

add_library(pob-compiler-options INTERFACE)
target_compile_options(pob-compiler-options INTERFACE
    ${POB_CLANG_WARNING_FLAGS}
    -Wno-unused-parameter
    ${POB_CLANG_HARDENING_FLAGS}
    "$<$<CONFIG:Debug>:-O0;-g3;-fno-optimize-sibling-calls>"
    "$<$<CONFIG:Debug,RelWithDebInfo>:-fno-omit-frame-pointer>"
    "$<$<COMPILE_LANGUAGE:C>:-Werror=implicit-function-declaration>")
target_compile_definitions(pob-compiler-options INTERFACE
    "$<$<CONFIG:Debug>:_DEBUG;_GLIBCXX_ASSERTIONS>"
    "POB_RUNTIME_DIAGNOSTICS=$<BOOL:${POB_RUNTIME_DIAGNOSTICS}>")
# The imported runtime implements many callback interfaces with unused arguments.
# Keep other unused-variable/function diagnostics enabled.
function(pob_configure_runtime_warnings target)
    target_link_libraries(${target} PRIVATE pob-compiler-options)
endfunction()
