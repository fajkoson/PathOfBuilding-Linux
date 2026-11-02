#!/usr/bin/env python3
"""Install pinned build tools into the disposable out/ tree."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download(entry, directory):
    archive = directory / entry["archive"]
    if archive.is_file() and digest(archive) == entry["sha256"]:
        return archive
    partial = archive.with_suffix(archive.suffix + ".part")
    print(f"Downloading {entry['archive']}...", flush=True)
    subprocess.run(
        ["curl", "--fail", "--location", "--silent", "--show-error",
         "--retry", "3", "--retry-delay", "1", "--connect-timeout", "20",
         "--max-time", "300", "--output", str(partial), entry["url"]],
        check=True,
    )
    if digest(partial) != entry["sha256"]:
        partial.unlink()
        raise RuntimeError(f"SHA-256 mismatch for {entry['archive']}")
    partial.replace(archive)
    return archive


def extract(archive, destination, kind):
    if kind == "tar":
        with tarfile.open(archive) as source:
            source.extractall(destination, filter="data")
    else:
        with zipfile.ZipFile(archive) as source:
            for member in source.infolist():
                target = (destination / member.filename).resolve()
                mode = member.external_attr >> 16
                if not target.is_relative_to(destination.resolve()) or stat.S_ISLNK(mode):
                    raise RuntimeError(f"Unsafe ZIP member: {member.filename}")
            source.extractall(destination)
    children = list(destination.iterdir())
    return children[0] if len(children) == 1 and children[0].is_dir() else destination


def install(name, entry, tools, downloads, logs):
    destination = tools / f"{name}-{entry['version']}"
    identity = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
    marker = destination / ".bootstrap-id"
    programs = entry["executables"]
    cached = marker.is_file() and marker.read_text() == identity
    if not cached or not all(os.access(destination / p, os.X_OK) for p in programs.values()):
        archive = download(entry, downloads)
        with tempfile.TemporaryDirectory(prefix=f".{name}-", dir=tools) as temporary:
            unpacked = Path(temporary) / "unpacked"
            unpacked.mkdir()
            package = extract(archive, unpacked, entry["format"])
            if entry["build"] == "make":
                print(f"Building {name} {entry['version']} with Clang...", flush=True)
                log = logs / f"bootstrap-{name}.log"
                command = [
                    "make", "-f", "unix/Makefile", "generic",
                    f"CC={shutil.which('clang')} -std=gnu89",
                ]
                with log.open("w") as output:
                    result = subprocess.run(command, cwd=package, stdout=output,
                                            stderr=subprocess.STDOUT)
                if result.returncode:
                    raise RuntimeError(f"{name} build failed; see {log}")
            for relative in programs.values():
                program = package / relative
                if not program.is_file():
                    raise RuntimeError(f"Archive did not provide {name}: {relative}")
                program.chmod(program.stat().st_mode | 0o755)
            (package / ".bootstrap-id").write_text(identity)
            if destination.exists():
                shutil.rmtree(destination)
            package.replace(destination)
    binary_dir = tools / "bin"
    binary_dir.mkdir(exist_ok=True)
    for command, relative in programs.items():
        link = binary_dir / command
        target = Path("..") / destination.name / relative
        if link.is_symlink() and os.readlink(link) == str(target):
            continue
        link.unlink(missing_ok=True)
        link.symlink_to(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if platform.system() != "Linux" or platform.machine() not in {"x86_64", "AMD64"}:
        raise RuntimeError("The pinned bootstrap binaries currently support x86-64 Linux")
    if sys.version_info < (3, 12):
        raise RuntimeError("Bootstrap requires Python 3.12 or newer")
    required = ("clang", "clang++", "make", "git", "curl", "tar")
    missing = [tool for tool in required if not shutil.which(tool)]
    if missing:
        raise RuntimeError("Missing host prerequisites: " + ", ".join(missing)
                           + ". See docs/linux-build.md")
    output = ROOT / "out"
    tools = output / "tools"
    downloads = output / "downloads/bootstrap"
    logs = output / "logs"
    for directory in (tools, downloads, logs):
        directory.mkdir(parents=True, exist_ok=True)
    lock = json.loads((ROOT / "cmake/bootstrap-tools.lock.json").read_text())
    with (tools / ".bootstrap.lock").open("w") as mutex:
        fcntl.flock(mutex, fcntl.LOCK_EX)
        for name, entry in lock.items():
            install(name, entry, tools, downloads, logs)
    if not args.quiet:
        print(f"Build tools ready: {tools / 'bin'}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.CalledProcessError, tarfile.TarError,
            zipfile.BadZipFile) as error:
        print(f"Bootstrap failed: {error}", file=sys.stderr)
        sys.exit(1)
