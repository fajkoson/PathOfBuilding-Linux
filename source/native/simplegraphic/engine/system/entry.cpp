// SimpleGraphic Engine
// (c) David Gowor, 2014
// Native Linux runtime entry point; preserve the upstream host API name.
#include "system/linux/sys_local.h"

extern "C" int RunLuaFileAsWin(int argc, char** argv)
{
    auto* sys = new sys_main_c;
    while (sys->Run(argc, argv)) {}
    delete sys;
    return 0;
}
