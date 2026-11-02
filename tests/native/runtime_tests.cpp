#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <tuple>
#include <unistd.h>
#include <pwd.h>

using byte = unsigned char;
class IConsole;
class sys_IConsole;
class sys_IVideo;
#include "system/sys_main.h"

// Platform functions exported by the actual runtime shared library.
std::tuple<std::optional<std::filesystem::path>, std::optional<std::string>> FindUserPath();

namespace fs = std::filesystem;

void require(bool condition, const std::string& message)
{
    if (!condition) throw std::runtime_error(message);
}

class ScratchDirectory {
public:
    fs::path path;
    ScratchDirectory()
    {
        auto pattern = (fs::current_path() / "runtime-tests-XXXXXX").string();
        auto result = mkdtemp(pattern.data());
        if (!result) throw std::runtime_error("Cannot create test directory");
        path = result;
    }
    ~ScratchDirectory()
    {
        std::error_code error;
        fs::remove_all(path, error);
    }
};

class Environment {
    std::string name;
    std::optional<std::string> previous;
public:
    explicit Environment(const char* variable) : name(variable)
    {
        if (auto value = std::getenv(variable)) previous = value;
    }
    void set(const char* value)
    {
        require((value ? setenv(name.c_str(), value, 1) : unsetenv(name.c_str())) == 0,
                "Cannot update test environment");
    }
    ~Environment()
    {
        if (previous) setenv(name.c_str(), previous->c_str(), 1);
        else unsetenv(name.c_str());
    }
};

void file_search()
{
    ScratchDirectory scratch;
    auto root = scratch.path / "Builds with spaces";
    fs::create_directories(root / "Nested" / "Deeper");
    std::ofstream(root / "Character.xml") << "build";
    std::ofstream(root / "ignore.txt") << "ignore";
    std::ofstream(root / "Nested" / "Deeper" / "Witch.xml") << "nested";

    find_c directory;
    require(directory.FindFirst(root / "Nested"), "Exact directory search failed");
    require(directory.isDirectory && directory.fileSize == 0, "Directory must have size zero");
    require(!directory.FindNext(), "Exact directory search returned extra entries");
    require(!directory.FindNext(), "Exhausted search must stay exhausted");

    find_c mixed;
    require(mixed.FindFirst(root / "*"), "Mixed search failed");
    int folders = 0, files = 0;
    do {
        if (mixed.isDirectory) {
            ++folders;
            require(mixed.fileSize == 0, "Directory in mixed search must have size zero");
        } else {
            ++files;
            require(mixed.fileSize == fs::file_size(root / mixed.fileName), "Wrong file size");
        }
    } while (mixed.FindNext());
    require(folders == 1 && files == 2, "Mixed enumeration missed entries");

    find_c xml;
    require(xml.FindFirst(root / "*.XML"), "Case-insensitive XML glob failed");
    require(xml.fileName == "Character.xml" && xml.fileSize == 5 && !xml.isDirectory,
            "XML search returned wrong metadata");
    require(!xml.FindNext(), "XML glob matched a non-XML entry");
    find_c nested;
    require(nested.FindFirst(root / "Nested" / "Deeper" / "*.xml"), "Nested build not found");
    require(nested.fileName == "Witch.xml" && nested.fileSize == 6, "Wrong nested build metadata");
    find_c empty;
    require(!empty.FindFirst(root / "missing*.xml"), "Unmatched glob must be empty");
    fs::create_directory(root / "Empty");
    require(!empty.FindFirst(root / "Empty" / "*"), "Empty directory must have no entries");
    require(!empty.FindFirst(root / "Missing" / "*"), "Missing directory must have no entries");
}

void user_paths()
{
    Environment xdg("XDG_DATA_HOME"), home("HOME");
    home.set("/test/home with spaces");
    xdg.set("/test/custom data");
    auto check = [](const fs::path& expected) {
        auto [path, error] = FindUserPath();
        require(path && *path == expected && !error, "Unexpected user-data path; expected " + expected.string());
    };
    check("/test/custom data");
    xdg.set(nullptr);
    check("/test/home with spaces/.local/share");
    xdg.set("");
    check("/test/home with spaces/.local/share");
    xdg.set("relative/data");
    check("/test/home with spaces/.local/share");
    home.set(nullptr);
    auto account = getpwuid(getuid());
    require(account != nullptr, "Cannot obtain account home directory");
    check(fs::path(account->pw_dir) / ".local/share");
}

int main(int argc, char** argv)
{
    try {
        require(argc == 2, "Expected file-search or user-paths");
        std::string suite = argv[1];
        if (suite == "file-search") file_search();
        else if (suite == "user-paths") user_paths();
        else throw std::runtime_error("Unknown suite: " + suite);
        std::cout << "PASS: " << suite << '\n';
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "FAIL: " << error.what() << '\n';
        return 1;
    }
}
