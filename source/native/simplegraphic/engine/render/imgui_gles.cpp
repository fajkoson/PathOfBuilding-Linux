// Use the renderer's GLFW-resolved GLES functions. Linking ImGui directly
// to ANGLE on Linux mixes ANGLE entry points with a native EGL context.
#include <glad/gles2.h>
#include <imgui_impl_opengl3.cpp>
