# Native Linux runtime. Configure from the repository root.
project(SimpleGraphic LANGUAGES C CXX)
list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")
find_package(unofficial-angle CONFIG REQUIRED)
find_package(CMakeRC CONFIG REQUIRED)
find_package(CURL CONFIG REQUIRED)
find_package(fmt CONFIG REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(gli CONFIG REQUIRED)
find_package(glm CONFIG REQUIRED)
find_package(LuaJIT REQUIRED)
find_package(Microsoft.GSL CONFIG REQUIRED)
find_package(PkgConfig REQUIRED)
find_package(re2 CONFIG REQUIRED)
find_package(sol2 CONFIG REQUIRED)
find_package(Threads REQUIRED)
find_package(zstd REQUIRED)
find_package(ZLIB REQUIRED)
find_package(WebP REQUIRED)

set(SIMPLEGRAPHIC_SOURCES
    "config.h"
    "dep/stb/stb_image.h"
    "dep/stb/stb_image_resize.h"
    "dep/stb/stb_image_write.h"
    "engine/common.h"
    "engine/common/base64.c"
    "engine/common/base64.h"
    "engine/common/common.cpp"
    "engine/common/console.cpp"
    "engine/common/console.h"
    "engine/common/keylist.h"
    "engine/common/memtrak3.cpp"
    "engine/common/memtrak3.h"
    "engine/common/streams.cpp"
    "engine/common/streams.h"
    "engine/core/core_compress.cpp"
    "engine/core/core_compress.h"
    "engine/core/core_config.cpp"
    "engine/core/core_config.h"
    "engine/core/core_image.cpp"
    "engine/core/core_image.h"
    "engine/core/core_main.cpp"
    "engine/core/core_main.h"
    "engine/core/core_tex_manipulation.cpp"
    "engine/core/core_tex_manipulation.h"
    "engine/core/core_video.cpp"
    "engine/core/core_video.h"
    "engine/render/r_font.cpp"
    "engine/render/r_font.h"
    "engine/render/r_main.cpp"
    "engine/render/r_main.h"
    "engine/render/r_texture.cpp"
    "engine/render/r_texture.h"
    "engine/system/linux/sys_local.h"
    "engine/system/linux/sys_main.cpp"
    "engine/system/linux/sys_opengl.cpp"
    "engine/system/linux/sys_video.cpp"
    "engine/system/linux/sys_console_unix.cpp"
    "engine/system/sys_console.h"
    "engine/system/sys_main.h"
    "engine/system/sys_opengl.h"
    "engine/system/sys_video.h"
    "engine/system/entry.cpp"
    "ui.h"
    "ui_api.cpp"
    "ui_console.cpp"
    "ui_console.h"
    "ui_debug.cpp"
    "ui_debug.h"
    "ui_local.h"
    "ui_main.cpp"
    "ui_main.h"
    "ui_subscript.cpp"
    "ui_subscript.h"
)

add_library(SimpleGraphic SHARED ${SIMPLEGRAPHIC_SOURCES})
pob_configure_runtime_warnings(SimpleGraphic)
cmrc_add_resource_library(SimpleGraphic-Assets ALIAS SimpleGraphic::Assets NAMESPACE SimpleGraphic)
cmrc_add_resources(SimpleGraphic-Assets
    assets/gles/display_render_target.frag
    assets/gles/display_render_target.vert
    assets/gles/tinted_texture.frag
    assets/gles/tinted_texture.vert)

target_compile_definitions(SimpleGraphic PRIVATE
    GLFW_INCLUDE_NONE GLM_ENABLE_EXPERIMENTAL SIMPLEGRAPHIC_EXPORTS)
target_include_directories(SimpleGraphic PUBLIC
    "${CMAKE_CURRENT_SOURCE_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}/engine")
target_include_directories(SimpleGraphic SYSTEM PRIVATE dep/glad/include dep/stb)

add_library(cmp_core STATIC
    ${POB_compressonator_SOURCE_DIR}/cmp_core/source/cmp_core.cpp
    ${POB_compressonator_SOURCE_DIR}/cmp_core/shaders/bc3_encode_kernel.cpp
    ${POB_compressonator_SOURCE_DIR}/cmp_core/shaders/bc7_encode_kernel.cpp)
target_include_directories(cmp_core PRIVATE
    ${POB_compressonator_SOURCE_DIR}/applications/_libs/cmp_math)
target_include_directories(cmp_core SYSTEM PUBLIC
    ${POB_compressonator_SOURCE_DIR}/cmp_core/shaders
    ${POB_compressonator_SOURCE_DIR}/cmp_core/source)

add_library(imgui STATIC
    ${POB_imgui_SOURCE_DIR}/imgui.cpp
    ${POB_imgui_SOURCE_DIR}/imgui_demo.cpp
    ${POB_imgui_SOURCE_DIR}/imgui_draw.cpp
    ${POB_imgui_SOURCE_DIR}/imgui_tables.cpp
    ${POB_imgui_SOURCE_DIR}/imgui_widgets.cpp
    ${POB_imgui_SOURCE_DIR}/backends/imgui_impl_glfw.cpp
    ${POB_imgui_SOURCE_DIR}/misc/cpp/imgui_stdlib.cpp
    engine/render/imgui_gles.cpp)
target_compile_definitions(imgui PUBLIC IMGUI_IMPL_OPENGL_ES2)
target_include_directories(imgui PRIVATE dep/glad/include)
target_include_directories(imgui SYSTEM PUBLIC
    ${POB_imgui_SOURCE_DIR}
    ${POB_imgui_SOURCE_DIR}/backends
    ${POB_imgui_SOURCE_DIR}/misc/cpp)
target_link_libraries(imgui PUBLIC unofficial::angle::libGLESv2 glfw)

target_link_options(SimpleGraphic PRIVATE "LINKER:--export-dynamic")
target_link_libraries(SimpleGraphic PRIVATE
    unofficial::angle::libEGL unofficial::angle::libGLESv2
    cmp_core fmt::fmt glfw gli glm::glm imgui LuaJIT::LuaJIT
    Microsoft.GSL::GSL re2::re2 SimpleGraphic::Assets Threads::Threads
    WebP::webpdecoder ZLIB::ZLIB zstd::libzstd_shared)

file(GLOB LCURL_SOURCES CONFIGURE_DEPENDS "${POB_lcurl_SOURCE_DIR}/src/*.c")
add_library(lcurl SHARED ${LCURL_SOURCES})
target_include_directories(lcurl PRIVATE "${POB_lcurl_SOURCE_DIR}/src")
target_link_libraries(lcurl PRIVATE CURL::libcurl LuaJIT::LuaJIT)

add_library(lua-utf8 SHARED "${POB_luautf8_SOURCE_DIR}/lutf8lib.c")
target_link_libraries(lua-utf8 PRIVATE LuaJIT::LuaJIT)

add_library(luasocket SHARED)
foreach(source IN ITEMS auxiliar buffer compat except inet io luasocket options select tcp timeout udp usocket)
    target_sources(luasocket PRIVATE "${POB_luasocket_SOURCE_DIR}/src/${source}.c")
endforeach()
target_link_libraries(luasocket PRIVATE LuaJIT::LuaJIT)

add_library(lzip SHARED libs/LZip/lzip.cpp)
target_link_libraries(lzip PRIVATE LuaJIT::LuaJIT ZLIB::ZLIB)

# The pinned Lua-cURL binding deliberately supports deprecated curl APIs.
# Keep type/control-flow warnings enabled; expose deprecations for dependency audits.
option(POB_SHOW_DEPENDENCY_DEPRECATIONS "Show deprecated APIs in pinned Lua-cURL" OFF)
if(NOT POB_SHOW_DEPENDENCY_DEPRECATIONS)
    target_compile_options(lcurl PRIVATE -Wno-deprecated-declarations)
endif()
target_compile_options(lcurl PRIVATE -Werror=return-type)
