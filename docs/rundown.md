# Linux source layout

- `source/lua/Launch.lua`: application entry point and development-mode setup.
- `source/lua/Modules/`, `source/lua/Classes/`: Lua application, calculations and UI.
- `source/lua/Data/`, `source/lua/TreeData/`, `source/lua/Assets/`: upstream game data and graphics.
- `source/lua/Export/`: upstream datamining and data-maintenance tooling. Some exporters
  retain Windows assumptions; they are not part of the Linux application build.
- `source/resources/lua/`: pure Lua dependencies; `source/resources/fonts/`: font assets.
- `source/native/launcher/`: Linux executable entry point and Lua module search paths.
- `source/native/simplegraphic/`: native rendering, input and Lua host sources.
- `cmake/`: dependency pins, Clang toolchain, build and staging configuration.
- `deploy/`: distribution planning and future installer definitions.
- `tools/scripts/`: build helpers and data-maintenance scripts.
- `tests/lua/`, `tests/`: Lua regression tests, maintenance tests and Linux test container.
- `source/resources/manifest.xml`, `source/resources/help.txt`, `source/resources/changelog.txt`: metadata and documents read by the app.
- `out/`: ignored build outputs, dependencies, logs, tools and future packages.

See [the Linux build guide](linux-build.md) for commands and current limitations.

## Upstream path mapping

| Upstream | Linux fork |
| --- | --- |
| `src/` | `source/lua/` |
| `runtime/lua/` | `source/resources/lua/` |
| `runtime/SimpleGraphic/Fonts/` | `source/resources/fonts/` |
| `manifest.xml`, `help.txt`, `changelog.txt` | `source/resources/` |
| `CHANGELOG.md` | `docs/upstream-changelog.md` |
| `CONTRIBUTING.md` | `docs/contributing.md` |
| `spec/` | `tests/lua/` |

Merge upstream content into these destinations to preserve the compact layout.
