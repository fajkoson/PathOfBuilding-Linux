# Linux distribution

Start with AppImage for downloadable Linux releases: it provides a single-file
application that runs without a traditional installer. See the
[AppImage packaging guide](https://docs.appimage.org/packaging-guide/index.html).
Build release payloads on an appropriately old supported base system and test
on the target distributions; packaging a CachyOS binary alone does not establish
cross-distribution compatibility. See
[AppImage best practices](https://docs.appimage.org/reference/best-practices.html).

Flatpak is a useful second distribution channel for managed updates and desktop
integration. Its runtime and sandbox require explicit filesystem, network and
graphics integration. See
[Flatpak concepts](https://docs.flatpak.org/en/latest/basic-concepts.html).

NSIS creates Windows installers, so reserve it for a future Windows package.
See the [NSIS project](https://nsis.sourceforge.io/Main_Page). Native .deb/.rpm
packages can be added through CPack when distribution-specific packages are
needed. Generated packages will go to out/installers/. Installer generation is
not implemented by the build/run scripts.

