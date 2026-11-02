# Contributing to the Linux fork

See [the Linux build guide](linux-build.md) for prerequisites and configuration.
Use `./pob.sh build` and `./pob.sh run`; all generated output belongs under `out/`.
Use Clang, CMake and Ninja, and keep third-party sources pinned in
`cmake/sources.lock.json`. Dependencies are fetched without submodules.

Keep Linux runtime changes in `source/native/` and `cmake/` where possible so upstream
Lua and datamined game-data updates remain straightforward to merge.

Lua regression tests live in `tests/lua/`. Run the Linux test container with:

```sh
docker compose -f tests/container/compose.yml run --rm busted-tests
```

The container recipe is `tests/container/Dockerfile`. Data maintenance helpers
live in `tools/scripts/`; the ascendancy helper is `tools/scripts/fix_ascendancy_positions.py`.

Build-tool bootstrap regression tests use only the Python standard library:

```sh
python3 -B -m unittest discover -s tests -p test_bootstrap.py -v
python3 -B -m unittest discover -s tests -p test_build_ui.py -v
```

The bootstrap itself runs automatically before CMake. Use
`./tools/scripts/bootstrap.sh` to prepare only the pinned build tools.

Run `./pob.sh test` (or `./pob.sh test --debug`) after native runtime changes.
C++ regression tests live in `tests/native/` and link the actual runtime.
See [the build guide](linux-build.md#native-c-regression-tests) for coverage and logs.
