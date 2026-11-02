#!/usr/bin/env python3
"""Run the Linux build with a compact, dependency-free terminal display."""

import argparse
import contextlib
import fcntl
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


CONFIGURATIONS = ("Debug", "RelWithDebInfo", "Release")


@contextlib.contextmanager
def workspace_lock(root):
    # Lock the directory inode: a lock file inside out/ would be deleted by --fresh.
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another build is active in this workspace") from error
        yield
    finally:
        os.close(descriptor)


def reset_output(root, configuration, fresh=False):
    if configuration not in CONFIGURATIONS:
        raise ValueError("Invalid build configuration")
    output = root / "out"
    target = output if fresh else output / "build" / configuration
    components = [output] if fresh else [output, output / "build", target]
    for component in components:
        if component.is_symlink():
            raise ValueError(f"Refusing to reset output through a symbolic link: {component}")
    if target.exists():
        if not target.is_dir():
            raise ValueError(f"Expected a generated output directory: {target}")
        shutil.rmtree(target)
    return target


def elapsed(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}m {seconds:02d}s"


def last_output(log):
    with log.open("rb") as source:
        source.seek(max(0, log.stat().st_size - 4096))
        lines = source.read().decode("utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        if line.strip():
            return re.sub(r"[\x00-\x1f\x7f]", " ", ANSI.sub("", line.strip()))
    return ""


class StageFailed(Exception):
    def __init__(self, label, log, code):
        self.label = label
        self.log = log
        self.code = code if code > 0 else 128 - code


class Interrupted(Exception):
    def __init__(self, number):
        self.number = number


def stop_process(process):
    # CMake, Ninja and compiler children share this private process group.
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        pass
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGKILL)
        process.wait()


class Display:
    def __init__(self, plain=False, verbose=False, stream=None):
        self.stream = stream if stream is not None else sys.stdout
        self.interactive = self.stream.isatty() and os.environ.get("TERM") != "dumb" and not plain
        self.color = self.interactive and "NO_COLOR" not in os.environ
        self.animate = self.interactive and not verbose
        self.verbose = verbose
        self.unicode = not plain
        try:
            "✓✗⠋".encode(getattr(self.stream, "encoding", None) or "utf-8")
        except UnicodeEncodeError:
            self.unicode = False
        self.separator = " · " if self.unicode else " | "

    def paint(self, text, color):
        return f"\033[{color}m{text}\033[0m" if self.color else text

    def write(self, text):
        self.stream.write(text)
        self.stream.flush()

    def __enter__(self):
        if self.animate:
            self.write("\033[?25l")
        return self

    def __exit__(self, *args):
        if self.animate:
            self.write("\r\033[2K\033[?25h")

    def start(self, index, total, label):
        if not self.animate:
            self.write(f"  -> [{index}/{total}] {label}\n")

    def progress(self, index, total, label, duration, detail):
        if not self.animate:
            return
        frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏" if self.unicode else "|/-\\"
        frame = frames[int(duration * 8) % len(frames)]
        prefix = f"  {frame} [{index}/{total}] {label}  {elapsed(duration)}"
        width = max(20, shutil.get_terminal_size((100, 24)).columns - 1)
        remaining = width - len(prefix) - 3
        suffix = f"{self.separator}{detail[:remaining]}" if remaining > 10 and detail else ""
        self.write("\r\033[2K" + self.paint(prefix, "36") + self.paint(suffix, "2"))

    def finish(self, index, total, label, duration, success):
        symbol = ("✓" if success else "✗") if self.unicode else ("[OK]" if success else "[FAIL]")
        if self.animate:
            self.write("\r\033[2K")
        self.write(self.paint(f"  {symbol} [{index}/{total}] {label}", "32" if success else "31")
                   + self.paint(f"  {elapsed(duration)}", "2") + "\n")


class Runner:
    def __init__(self, display, environment=None, cwd=ROOT):
        self.display = display
        self.environment = environment
        self.cwd = cwd

    def run(self, index, total, label, command, log):
        start = time.monotonic()
        self.display.start(index, total, label)
        with log.open("wb") as output, log.open("r", errors="replace") as live:
            try:
                process = subprocess.Popen(command, cwd=self.cwd, env=self.environment,
                                           stdout=output, stderr=subprocess.STDOUT,
                                           start_new_session=True)
            except OSError as error:
                output.write(f"{error}\n".encode())
                self.display.finish(index, total, label, time.monotonic() - start, False)
                raise StageFailed(label, log, 127) from error
            try:
                while process.poll() is None:
                    if self.display.verbose:
                        self.display.write(live.read())
                    else:
                        self.display.progress(index, total, label, time.monotonic() - start,
                                              last_output(log))
                    time.sleep(0.12)
                if self.display.verbose:
                    self.display.write(live.read())
            except (KeyboardInterrupt, Interrupted):
                stop_process(process)
                self.display.finish(index, total, label, time.monotonic() - start, False)
                raise
            self.display.finish(index, total, label, time.monotonic() - start, process.returncode == 0)
            if process.returncode:
                raise StageFailed(label, log, process.returncode)


def warning_count(log):
    return sum("warning:" in line.lower() or line.startswith("CMake Warning")
               for line in log.read_text(errors="replace").splitlines())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=CONFIGURATIONS, required=True)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("--test", action="store_true", help="Build and run native C++ regression tests")
    reset = parser.add_mutually_exclusive_group()
    reset.add_argument("--rebuild", action="store_true", help="Reset the selected build directory")
    reset.add_argument("--fresh", action="store_true", help="Reset all generated output and downloads")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be positive")
    with workspace_lock(ROOT):
        return run_build(args)


def run_build(args):
    logs = ROOT / "out/logs"
    environment = dict(os.environ)
    environment["PATH"] = f"{ROOT / 'out/tools/bin'}{os.pathsep}{environment.get('PATH', '')}"
    cmake = str(ROOT / "out/tools/bin/cmake")
    build = ROOT / "out/build" / args.config
    preset = {"Debug": "linux-debug", "RelWithDebInfo": "linux-relwithdebinfo", "Release": "linux-release"}[args.config]
    stages = [
        ("Prepare build tools", [sys.executable, str(ROOT / "tools/scripts/bootstrap.py"), "--quiet"], "bootstrap"),
        ("Configure & dependencies", [cmake, "--preset", preset], "configure"),
        ("Compile native runtime", [cmake, "--build", str(build), "--parallel", str(args.jobs),
                                    "--target", "pob-linux", "lcurl", "lzip", "lua-utf8", "luasocket"], "build"),
        ("Stage runtime & assets", [cmake, "--build", str(build), "--parallel", str(args.jobs),
                                    "--target", "stage"], "stage"),
    ]
    if args.test:
        stages[1][1].append("-DBUILD_TESTING=ON")
        stages.extend([
            ("Compile C++ tests", [cmake, "--build", str(build), "--parallel", str(args.jobs),
                                   "--target", "pob-native-tests"], "test-build"),
            ("Run C++ tests", [str(Path(cmake).resolve().with_name("ctest")), "--test-dir", str(build),
                               "--output-on-failure"], "test"),
        ])
    reset_requested = args.rebuild or args.fresh
    total = len(stages) + int(reset_requested)
    display = Display(args.plain, args.verbose)
    display.write("\n" + display.paint(f"  Path of Building{display.separator}Linux build", "1;32") + "\n")
    display.write(display.paint(f"  {args.config}{display.separator}Clang{display.separator}{args.jobs} jobs\n\n", "2"))
    start = time.monotonic()

    def terminate(number, frame):
        raise Interrupted(number)

    signal.signal(signal.SIGTERM, terminate)
    try:
        with display:
            if reset_requested:
                label = "Reset all generated output" if args.fresh else f"Reset {args.config} build"
                cleanup_start = time.monotonic()
                display.start(1, total, label)
                display.progress(1, total, label, 0, "")
                try:
                    target = reset_output(ROOT, args.config, fresh=args.fresh)
                    logs.mkdir(parents=True, exist_ok=True)
                    (logs / f"{args.config}-reset.log").write_text(f"Reset generated output: {target}\n")
                except (OSError, ValueError) as error:
                    display.finish(1, total, label, time.monotonic() - cleanup_start, False)
                    display.write(display.paint(f"\n  Reset failed: {error}\n", "31"))
                    return 1
                except (KeyboardInterrupt, Interrupted):
                    display.finish(1, total, label, time.monotonic() - cleanup_start, False)
                    raise
                display.finish(1, total, label, time.monotonic() - cleanup_start, True)
            else:
                logs.mkdir(parents=True, exist_ok=True)
            (ROOT / "out/installers").mkdir(parents=True, exist_ok=True)
            runner = Runner(display, environment)
            for index, (label, command, name) in enumerate(stages, 1 + int(reset_requested)):
                runner.run(index, total, label, command, logs / f"{args.config}-{name}.log")
    except StageFailed as failure:
        display.write(display.paint(f"\n  Build failed: {failure.label} (exit {failure.code})\n", "31"))
        display.write(f"  Full log: {failure.log}\n\n")
        for line in failure.log.read_text(errors="replace").splitlines()[-25:]:
            display.write(f"    {ANSI.sub('', line)}\n")
        return failure.code
    except (KeyboardInterrupt, Interrupted) as interruption:
        display.write(display.paint("\n  Build interrupted; child processes stopped.\n", "33"))
        return 130 if isinstance(interruption, KeyboardInterrupt) else 128 + interruption.number
    display.write(display.paint(f"\n  Build complete{display.separator}{elapsed(time.monotonic() - start)}\n", "1;32"))
    compile_warnings = warning_count(logs / f"{args.config}-build.log")
    configure_warnings = warning_count(logs / f"{args.config}-configure.log")
    if compile_warnings or configure_warnings:
        display.write(display.paint(f"  Warnings: {compile_warnings} compile, {configure_warnings} configure (see logs)\n", "33"))
    display.write(f"  Binary: {build / 'bin/pob-linux'}\n")
    display.write(f"  Run:    ./pob.sh run --{args.config.lower()}\n  Logs:   {logs}\n\n")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError) as error:
        print(f"Build failed: {error}", file=sys.stderr)
        sys.exit(1)
