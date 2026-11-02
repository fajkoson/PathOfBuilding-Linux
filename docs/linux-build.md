# Native Linux build

This fork runs the upstream Lua application in a native C++23 SimpleGraphic host.
The initial target is x86-64 Linux with Clang, libstdc++, CMake 3.25+ and Ninja.
The port is in development: a complete build and graphical smoke test are required
before claiming Linux support. Runtime resources live in source/resources/.
The initial GLFW configuration uses X11 (or XWayland in a Wayland session).
Native Wayland support is a later validation target.

## Dependencies

Application libraries are built from source through the imported SimpleGraphic
vcpkg manifest and its pinned baseline/custom ports. Direct source dependencies
are locked in cmake/sources.lock.json and fetched into out/deps.
Source archives are verified with SHA-256; vcpkg uses an exact Git revision in
a normal build-local checkout. No submodules or separate dependency commits
are required. The x64-linux-clang triplet selects Clang for both host
and target packages and uses shared third-party libraries where supported, ensuring the host and Lua
extensions share one LuaJIT runtime;
libc, libstdc++, display libraries and graphics drivers remain system dependencies.
No application library is installed globally.

`./build.sh` automatically bootstraps pinned CMake, Ninja, Zip and Unzip into
`out/tools/`, verifies their archive SHA-256 hashes, then fetches/builds the
application dependencies. Tool versions and hashes live in
`cmake/bootstrap-tools.lock.json`. Python 3.12+ is needed for the bootstrap.
Deleting the entire `out/` directory is supported: the next build recreates it.

Install the host compiler, base utilities and Linux SDK packages using your
distribution. On Arch/CachyOS the prerequisite set is:

```sh
sudo pacman -S --needed base-devel clang git curl tar pkgconf python libx11 libxrandr libxinerama libxcursor libxi libxkbcommon wayland wayland-protocols mesa libglvnd autoconf automake libtool
```

Additional dependency-specific tools may be reported by vcpkg during configure.
Do not use sudo for CMake, vcpkg or the application build.

## Configure and build

Use the single entry point from Bash, fish, or another calling shell:

```sh
./pob.sh build             # Release, the default
./pob.sh run               # Run Release
./pob.sh build --debug
./pob.sh run --debug
./pob.sh build --release -j 8
./pob.sh help              # Commands, options and saved-build location
```

`--release`, `--debug` and `--relwithdebinfo` select the build type for both
commands. Use the same type when building and running. Pass application arguments
after `--`, for example `./pob.sh run -- <argument>`.

The older `build.sh` and `run.sh` entry points remain available and default to
RelWithDebInfo. Their positional build type syntax is unchanged; `pob.sh` defaults
to Release for a simpler player workflow.

Build scripts configure CMake, fetch pinned dependencies, compile, and stage the
runtime. They can be called by absolute path from another working directory.
Use --help for options. POB_BUILD_JOBS sets the default parallel job count (8).
The default terminal view shows four stages: tools, configuration/dependencies,
compilation, and runtime staging. An active stage shows a spinner, elapsed time,
and the latest output line; completed stages receive green checks. Failed stages
show a red cross, the exit status, the log path, and the last 25 log lines.
Ctrl+C stops the active build process group and restores the terminal cursor.

```sh
./pob.sh build --verbose  # Stream full logs alongside stage results
./pob.sh build --plain    # Plain status lines without ANSI or animation
```

Redirected/non-terminal output does not contain ANSI controls. NO_COLOR disables
colors in an interactive terminal. Full output always goes to
out/logs/<configuration>-bootstrap.log, -configure.log, -build.log and -stage.log.
The summary reports warnings from this invocation's configure and compile logs.

For a clean rebuild, use:

```sh
./pob.sh build --rebuild
```

This removes only `out/build/Release/`, including its CMake cache, objects and
configuration-specific dependency installation. CMake configures from scratch
and recompiles the native application. Shared tools, fetched sources, downloads,
and the package cache remain available, as do other build configurations.

To reproduce deleting the whole output directory, use:

```sh
./pob.sh build --fresh
```

This removes all of `out/`: every configuration, tools, downloaded sources and
archives, local caches, logs, and generated installers. The bootstrap then
recreates the tools and downloads/builds dependencies at their pinned versions.
Sources, settings and saved builds outside out/ are preserved. Both flags add a
reset stage to the TUI, support --plain/--verbose, and are mutually exclusive.
A workspace lock rejects concurrent build-script invocations, preventing one
script from resetting another script's active build.
Symbolic links in the cleanup path are rejected.


The scripts automatically prepare `out/tools/bin` and add it to PATH for the
build process. No shell setup or system-wide tool installation is required.
To fetch/build only the managed build tools, run:

```sh
./tools/scripts/bootstrap.sh
```

This tool-only command does not yet configure or compile the application.
Clang, make, Git, curl, tar, Python and the operating-system SDK remain host
prerequisites; application libraries and managed tools are downloaded into out/.

Equivalent CMake presets are linux-debug, linux-relwithdebinfo and linux-release.
For example: cmake --preset linux-debug, then cmake --build --preset linux-debug.

```text
out/
  build/
    Debug/
      bin/                 # Executable, shared/static libraries and runtime assets
      CMakeFiles/          # Intermediate objects and build-system files
      vcpkg_installed/     # Per-configuration dependency installation
    RelWithDebInfo/
      bin/
    Release/
      bin/
  deps/                    # Shared, pinned dependency sources and their caches
  tools/                   # Pinned managed build tools
  downloads/bootstrap/     # Checksum-verified tool archives
  cache/vcpkg/             # Default package binary cache
  installers/              # Future distributable packages
  logs/                    # Configure/build logs
```

All generated output is ignored by Git. Obsolete build trees and Windows
binaries are removed. Build scripts save configure/build logs in out/logs/
and in-source CMake builds are rejected. The stage target copies fonts, Lua modules,
and privately built shared libraries into bin/, and links the application source/lua/
directory there for development. System libc, libstdc++ and graphics drivers
remain host dependencies. The development source symlink means bin/ is not yet
a standalone distributable; packaging must copy the application data and remove
build-machine paths before distribution.

## Distribution

See [deployment planning](../deploy/README.md) for AppImage/Flatpak recommendations.
Generated packages belong in out/installers/; installer generation is not implemented yet.

## Clang diagnostics

The Clang toolchain defines the project warning policy. `CompilerOptions.cmake`
applies it to the maintained native runtime and launcher, without injecting it
into vcpkg builds. Enabled options include `-Wall`, `-Wextra`, `-Wformat=2`,
`-Werror=format-security`, `-Werror=return-type`, and `-fstack-protector-strong`.
Debug and RelWithDebInfo also retain frame pointers. C targets using the policy
reject implicit function declarations. Optimizations remain configuration-specific;
no host-specific CPU or fast-math flags are added.

Unused callback parameters and nonliteral format strings in formatting wrappers
are exempted. Format-security checking and other unused-code diagnostics remain
active. Third-party include directories use CMake's SYSTEM classification.
The pinned Lua-cURL binding's deprecated curl APIs are quiet by default; configure
with `-DPOB_SHOW_DEPENDENCY_DEPRECATIONS=ON` to audit them. This suppression applies
to Lua-cURL alone, and its missing-return diagnostic is an error.

Tracked patches in `cmake/patches/` fix Lua-cURL return types, option argument types
and socket casts, plus Compressonator vector conversion and floating-point absolute
values. CMake applies them after verifying the pinned source archive. If a patch
changes and no longer applies to a reused source cache, remove that dependency's
`out/deps/<name>-*` directories and configure again.

Three explicit port warnings remain: subprocess launching, URL opening and global
cursor position queries are not yet implemented on Linux. These warnings are
intentionally kept visible; successful compilation does not validate those features.

## Source layout and updates

- CMakeLists.txt and CMakePresets.json: Linux build entry point and configurations.
- cmake/: dependency checks, Clang toolchain, vcpkg triplet and staging target.
- source/native/launcher/: executable entry point adapting arguments to SimpleGraphic.
- source/native/simplegraphic/: imported runtime source; original licensing retained.
- source/native/simplegraphic-upstream.txt: import provenance and exact revision.
- source/lua/: upstream Lua application and game data.
- source/resources/: fonts, Lua dependencies, manifest, help and changelog.
- docs/: project documentation and upstream Markdown changelog.
- tests/: Lua regression tests, maintenance tests and container setup.

Application updates are merged from upstream/dev into linux-support. Runtime
updates use git subtree pull --prefix=source/native/simplegraphic with the runtime's
repository URL and --squash. Follow the path mappings in [the source layout](rundown.md) when upstream
restores root resources or the old spec/runtime directories.
Update the provenance record and translate upstream dependency revisions into
cmake/sources.lock.json, including verified archive hashes. Remove any upstream
gitlinks and .gitmodules introduced by a runtime update. Dependencies are fetched
by CMake and must remain outside the tracked source tree.

Local AGENTS.md and .agents/skills are intentionally ignored and must be copied
separately when setting up another machine.

## Native C++ regression tests

```sh
./pob.sh test
./pob.sh test --debug
```

The test command configures/builds the application, compiles `pob-native-tests`,
and runs CTest with failure output. It uses the same stage UI and supports
`--release`, `--debug`, `--relwithdebinfo`, `-j`, `--verbose`, `--plain`,
`--rebuild` and `--fresh`. Release is the default. Build and test logs are saved
under `out/logs/`, including `<configuration>-test-build.log` and
`<configuration>-test.log`.

The suites link the actual SimpleGraphic library and run without a display:

- `native-file-search`: exact directory queries, mixed file/folder listings,
  zero-size directory metadata, nested builds in paths with spaces,
  case-insensitive XML globs, real file sizes and empty/missing directories.
- `native-user-paths`: absolute XDG override, HOME fallback, empty/relative XDG
  rejection and the account-home fallback when HOME is unset.

Checks use explicit failures rather than `assert()`, so they also run in Release.
Each file-search run creates and removes a unique temporary directory beneath
`out/build/<configuration>/tests/native/`. Environment changes affect only the
test process; no real builds or settings are read or written. These tests do not
validate GUI behavior, Lua calculations, network imports or interactive saving.

The targets are controlled by CMake's `BUILD_TESTING` option. Ordinary builds do
not compile the test executable. For direct CMake/CTest use after configuring:

```sh
./out/tools/bin/cmake --build out/build/Release --target pob-native-tests
./out/tools/bin/cmake --build out/build/Release --target test
```

## Launch display

`./pob.sh run` reports native initialization, graphics initialization, planner/tree
loading and item loading as stages. Completion is based on runtime log messages;
"Application ready" is shown after item data loads. It waits for the application
to close. `--plain` disables colors and animation; `--verbose` streams full output
alongside the status. Both options also work with the older `run.sh` entry point.

Each launch writes a separate `out/logs/<configuration>-runtime-<id>.log` so
simultaneous launches do not overwrite each other's output. Startup warning counts
and runtime errors remain visible. Nonzero exits show the last 25 log lines.
Ctrl+C stops the launched process group and restores the terminal cursor.

## Debugging

```sh
./pob.sh build --debug
./pob.sh run --debug
```

Debug uses `-O0 -g3`, frame pointers and `-fno-optimize-sibling-calls` for readable
native backtraces. Project targets define `_DEBUG` (the runtime's existing Debug
switch) and `_GLIBCXX_ASSERTIONS` for additional libstdc++ checks. Standard C/C++
assertions remain enabled. These project flags do not alter fetched dependencies'
compiler options. RelWithDebInfo keeps optimized code, debug symbols and frame
pointers; Release favors optimized execution.

`POB_RUNTIME_DIAGNOSTICS` is a CMake option, defaulting to ON for Debug and OFF
otherwise on a new configure. It prints compiler, architecture, runtime/script
paths, user data base and CPU thread count at startup. All console output is saved to a per-launch runtime log under `out/logs/`.
Use `./pob.sh run --debug --verbose` to also stream it to the terminal. There is no
separate hidden set of verbose Debug messages in the upstream host.

To override diagnostics in an existing configuration:

```sh
./out/tools/bin/cmake --preset linux-debug -DPOB_RUNTIME_DIAGNOSTICS=OFF
./pob.sh build --debug
```

Use `ON` to enable it again, including in Release via `linux-release`. The cache
keeps an explicit setting until changed or reset with `--rebuild`/`--fresh`.
`--verbose` controls build output, not runtime logging.

Save runtime messages or attach a debugger (install GDB separately if needed):

```sh
./pob.sh run --debug --verbose 2>&1 | tee out/logs/Debug-runtime.log
gdb --args out/build/Debug/bin/pob-linux
```

In GDB, use `run`, then `bt` after a crash.

## Saved builds and settings

Linux always uses a per-user data folder, including development builds:

```text
~/.local/share/Path of Building/
├── Builds/       # Build XML files and optional subfolders
└── Settings.xml  # Application settings
```

An absolute `XDG_DATA_HOME` replaces `~/.local/share`; empty or relative values
fall back to the default. Missing directories are created automatically.
The app's **Build save path** setting can override the builds folder. Debug,
RelWithDebInfo and Release share these settings and builds. Neither rebuild option
removes them. Copy build XML files directly into `Builds/`; put `Settings.xml`
one level above it, with the app closed.

Earlier repository-local saves in `source/lua/Builds/` and `source/lua/Settings.xml`
are preserved but no longer loaded by default. Copy them to the data folder to
continue using them, taking care not to overwrite newer files.

## Validation milestones

1. Configure the Linux presets with Clang and build the stage target.
2. Verify native Lua modules load against the pinned LuaJIT ABI.
3. Launch a window and verify fonts, tree rendering, keyboard, mouse and clipboard.
4. Load/save a build; check calculations, character import and network requests.
5. Audit updater behavior before using upstream automatic updates on Linux.

Installer generation and Linux CI follow functional validation. Windows release, installer and runtime-update workflows are removed.
The Linux Lua regression-test container is retained under tests/container/.

## Initial verification on CachyOS

Clang 23.1.4 configured and built both Debug and RelWithDebInfo runtimes. The native Lua modules
lcurl.safe, lua-utf8, socket and lzip loaded against the pinned LuaJIT, including
a regression check for an unset environment variable. The GUI initialized its
renderer and loaded the 3.29 passive tree, uniques and rares during startup smoke tests in both configurations.
The first Debug session was closed manually. The log reports a missing PassiveMasteryConnectedButton.png
asset in the upstream application data; that asset has not been replaced here.

Existing build loading and nested folder scanning have since been verified.
This startup check does not validate interactive editing, saving, clipboard,
character imports, or networking. Those remain the next functional checks.
The Linux ImGui backend uses the same GLFW-resolved GLES function table as the
renderer, avoiding ANGLE calls against a native EGL context.

The obsolete runtime-win32.zip is deleted because the native Linux build does
not use it. If an upstream merge restores the archive, remove it again.
