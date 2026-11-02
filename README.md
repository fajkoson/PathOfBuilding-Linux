# Path of Building for Linux

A fork of [Path of Building Community](https://github.com/PathOfBuildingCommunity/PathOfBuilding),
cluelessly ported to Linux. A native Linux build of the Path of Exile build planner.

## Get started

1. Install the prerequisites in [the Linux build guide](docs/linux-build.md#dependencies).
2. Build and run from the repository folder:

```sh
./pob.sh build
./pob.sh run
```

Release is the default. The first build downloads tools and builds dependencies,
so it takes longer. Later builds reuse them. Run these commands as your normal
user, without sudo.

## Commands

| Command | What it does |
| --- | --- |
| `./pob.sh build` | Configure and build Release |
| `./pob.sh run` | Start Release |
| `./pob.sh test` | Build and run native C++ regression tests |
| `./pob.sh build --rebuild` | Fresh configure and compile; keep cached dependencies |
| `./pob.sh build --fresh` | Delete all `out/`, then download and build everything again |
| `./pob.sh help` | Show commands and saved-build locations |

For Debug, use `./pob.sh build --debug` and `./pob.sh run --debug`.
Explicit `--release` and `--relwithdebinfo` are also supported for build and run.
Build options include `-j 8`, `--verbose` for full output, and `--plain` to disable
colors and animation. Logs are in `out/logs/`; binaries are in
`out/build/<build type>/bin/`. `--fresh` also removes other build types and installers.

## C++ tests

```sh
./pob.sh test           # Build and test Release
./pob.sh test --debug   # Build and test Debug
```

Tests call the actual native runtime without opening a window. They cover nested
build folders, XML filename matching, file sizes, empty/missing folders, and Linux
user-data path selection. Temporary files stay under `out/`; your saved builds
and settings are untouched. Test results are in `out/logs/<build type>-test.log`.

## Debugging

```sh
./pob.sh build --debug
./pob.sh run --debug
```

Debug enables full compiler symbols, disables optimization, enables C++ assertions,
and prints extra native startup details in the terminal. Use `--verbose` to also see existing application
messages in the terminal. To save the output:

```sh
./pob.sh run --debug --verbose 2>&1 | tee out/logs/Debug-runtime.log
```

Use `./pob.sh build --debug --verbose` for full **compilation** output.
See [debug options](docs/linux-build.md#debugging) for CMake controls.

## Launch status and logs

`./pob.sh run` shows startup stages with green checks, then stays attached until
you close the app. Full runtime output is saved to a separate log for each launch
in `out/logs/` (the exact path is printed). Startup warnings are counted; failures
show the end of the log.

```sh
./pob.sh run --verbose   # Stream native and Lua messages too
./pob.sh run --plain     # Status without colors or animation
```

## Saved builds

Copy your build **XML files** into:

```text
~/.local/share/Path of Building/Builds/
```

New builds are saved there too. Subfolders are supported. Settings are stored at
`~/.local/share/Path of Building/Settings.xml`, outside the `Builds/` folder.
These files belong to your Linux user, outside the repository and installation.
Rebuilding or deleting `out/` preserves them.

An absolute `XDG_DATA_HOME` replaces `~/.local/share`. You can choose another builds
folder using **Build save path** in the app's settings.

If you used an earlier development version, copy XML files from
`source/lua/Builds/` into the new builds folder. Existing files are left untouched.
Copy an old `Settings.xml` into the data folder only while the app is closed.

## Status

The app starts and existing saved builds load successfully. Native directory
scanning supports nested build folders. Debug, RelWithDebInfo and Release have
passed compilation checks. Interactive saving, clipboard and character imports
still need functional verification. Installer generation is not implemented yet.

## Upstream updates

The Linux branch receives application and game-data updates from
[PathOfBuildingCommunity/PathOfBuilding](https://github.com/PathOfBuildingCommunity/PathOfBuilding).
Native runtime provenance is recorded in `source/native/simplegraphic-upstream.txt`.
Third-party sources are pinned and fetched by CMake without Git submodules.
See [contribution instructions](docs/contributing.md) and [source layout](docs/rundown.md).

## Licence
[MIT](https://opensource.org/licenses/MIT)

For 3rd-party licences, see [LICENSE](LICENSE.md).
The licencing information is considered to be part of the documentation.

## Repository layout

- `source/`: Lua application, native runtime, and runtime resources.
- `cmake/`: build configuration and pinned dependency fetching.
- `tools/scripts/`: development and data-maintenance helpers.
- `tests/`: regression tests and Linux test-container setup.
- `docs/`: build guide, architecture and contribution instructions.
- `deploy/`: Linux distribution planning.
- `out/`: ignored downloads, build output, logs and packages.
