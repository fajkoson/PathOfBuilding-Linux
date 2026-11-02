#!/usr/bin/env python3
"""Launch PoB with terminal stages and a complete runtime log."""

import argparse
import os
import signal
import subprocess
import time

if __package__:
    from .build import Display, Interrupted, ROOT, elapsed, stop_process
else:
    from build import Display, Interrupted, ROOT, elapsed, stop_process

STAGES = (
    ("Initialize native runtime", "Running script..."),
    ("Initialize graphics", "Renderer initialised"),
    ("Load planner and passive tree", "Startup time:"),
    ("Load item data", "Rares loaded"),
)


def launch(command, configuration, display, log, cwd=ROOT):
    started = stage_started = time.monotonic()
    stage = 0
    warnings = 0
    pending = ""
    error_reported = False
    display.write(f"\n  Path of Building{display.separator}Linux\n"
                  f"  {configuration}{display.separator}Starting application\n"
                  f"  Log: {log}\n\n")
    display.start(1, len(STAGES), STAGES[0][0])
    with log.open("wb") as output, log.open(errors="replace") as live:
        process = subprocess.Popen(command, cwd=cwd, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        try:
            while True:
                text = live.read()
                if display.verbose:
                    display.write(text)
                pending += text
                lines = pending.split("\n")
                pending = lines.pop()
                for line in lines:
                    warnings += "warning:" in line.lower()
                    if ("--- ERROR ---" in line or "--- SCRIPT ERROR ---" in line) and not error_reported:
                        if display.animate:
                            display.write("\r\033[2K")
                        display.write(display.paint(f"  Runtime error reported. See {log}\n", "31"))
                        error_reported = True
                    if stage < len(STAGES) and STAGES[stage][1] in line:
                        display.finish(stage + 1, len(STAGES), STAGES[stage][0],
                                       time.monotonic() - stage_started, True)
                        stage += 1
                        stage_started = time.monotonic()
                        if stage < len(STAGES):
                            display.start(stage + 1, len(STAGES), STAGES[stage][0])
                        else:
                            display.write(display.paint("\n  Application ready", "32")
                                          + f"{display.separator}{elapsed(time.monotonic() - started)}\n")
                            if warnings:
                                display.write(display.paint(f"  Startup warnings: {warnings} (see runtime log)\n", "33"))
                            display.write("  Close the application window to exit.\n\n")
                            if display.animate:
                                display.write("\033[?25h")
                code = process.poll()
                # Drain output written immediately before the child exited.
                if code is not None and not text:
                    break
                if stage < len(STAGES):
                    display.progress(stage + 1, len(STAGES), STAGES[stage][0],
                                     time.monotonic() - stage_started, "")
                time.sleep(0.10)
        except (KeyboardInterrupt, Interrupted):
            stop_process(process)
            display.write("\n  Application stopped.\n")
            return 130
    if stage < len(STAGES):
        display.finish(stage + 1, len(STAGES), STAGES[stage][0],
                       time.monotonic() - stage_started, False)
    if code or error_reported:
        display.write(display.paint(f"  Application exited with status {code}. Log: {log}\n", "31"))
        if not display.verbose:
            display.write("\n" + "\n".join(log.read_text(errors="replace").splitlines()[-25:]) + "\n")
    else:
        display.write(f"  Application closed{display.separator}{elapsed(time.monotonic() - started)}\n")
    return code if code >= 0 else 128 - code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, choices=("Debug", "Release", "RelWithDebInfo"))
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--plain", action="store_true")
    parser.add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    binary = ROOT / "out/build" / args.config / "bin/pob-linux"
    if not os.access(binary, os.X_OK):
        parser.exit(1, f"Build first: ./pob.sh build --{args.config.lower()}\n")
    logs = ROOT / "out/logs"
    logs.mkdir(parents=True, exist_ok=True)
    log = logs / f"{args.config}-runtime-{time.time_ns()}-{os.getpid()}.log"
    arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
    def interrupted(number, frame):
        raise Interrupted(number)
    previous = signal.signal(signal.SIGTERM, interrupted)
    try:
        with Display(args.plain, args.verbose) as display:
            return launch([str(binary), *arguments], args.config, display, log)
    finally:
        signal.signal(signal.SIGTERM, previous)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except OSError as error:
        raise SystemExit(f"Could not launch application: {error}")
