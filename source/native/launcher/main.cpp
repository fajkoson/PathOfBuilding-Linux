#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <string>
#include <vector>

extern "C" int RunLuaFileAsWin(int argc, char** argv);

int main(int argc, char** argv)
{
    try {
        // SimpleGraphic expects the script path as argv[0], not the executable.
        const auto runtime = std::filesystem::canonical("/proc/self/exe").parent_path();
        const std::string lua_path = (runtime / "lua/?.lua").string() + ";" +
            (runtime / "lua/?/init.lua").string() + ";./?.lua;./?/init.lua";
        const std::string lua_cpath = (runtime / "?.so").string();
        if (setenv("LUA_PATH", lua_path.c_str(), 1) != 0 ||
            setenv("LUA_CPATH", lua_cpath.c_str(), 1) != 0) {
            std::cerr << "Path of Building: cannot configure Lua module paths\n";
            return 1;
        }
        std::string script = (runtime / "src/Launch.lua").string();
        std::vector<char*> arguments{script.data()};
        for (int i = 1; i < argc; ++i) arguments.push_back(argv[i]);
        const int count = static_cast<int>(arguments.size());
        arguments.push_back(nullptr);
        return RunLuaFileAsWin(count, arguments.data());
    } catch (const std::exception& error) {
        std::cerr << "Path of Building: " << error.what() << '\n';
        return 1;
    }
}
