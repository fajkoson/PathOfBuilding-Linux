find_program(POB_CLANG_C NAMES clang REQUIRED)
find_program(POB_CLANG_CXX NAMES clang++ REQUIRED)
set(CMAKE_C_COMPILER "${POB_CLANG_C}" CACHE FILEPATH "C compiler" FORCE)
set(CMAKE_CXX_COMPILER "${POB_CLANG_CXX}" CACHE FILEPATH "C++ compiler" FORCE)
# vcpkg sets CMAKE_SYSTEM_NAME for Linux triplets, so also identify the CPU.
set(CMAKE_SYSTEM_PROCESSOR x86_64 CACHE STRING "Target processor")
set(CMAKE_POSITION_INDEPENDENT_CODE ON CACHE BOOL "Build dependencies usable in shared libraries")

# Project targets consume these through CompilerOptions.cmake. Keep warning
# policy out of global C/C++ flags so it does not leak into vcpkg builds.
set(POB_CLANG_WARNING_FLAGS
    -Wall -Wextra -Wformat=2 -Wno-format-nonliteral
    -Werror=format-security -Werror=return-type
    CACHE INTERNAL "Warnings for native project targets")
set(POB_CLANG_HARDENING_FLAGS -fstack-protector-strong
    CACHE INTERNAL "Hardening for native project targets")
