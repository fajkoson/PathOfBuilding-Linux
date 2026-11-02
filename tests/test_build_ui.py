import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.scripts import build


class BuildUiTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "out/tests"
        root.mkdir(parents=True, exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.output = io.StringIO()
        self.display = build.Display(plain=True, stream=self.output)
        self.runner = build.Runner(self.display, cwd=self.root)

    def test_success_keeps_full_output_in_log_without_terminal_escapes(self):
        log = self.root / "success.log"
        command = [sys.executable, "-c", "import sys; print('compiler output'); print('diagnostic', file=sys.stderr)"]
        self.runner.run(1, 4, "Compile", command, log)
        self.assertIn("compiler output", log.read_text())
        self.assertIn("diagnostic", log.read_text())
        self.assertIn("[OK] [1/4] Compile", self.output.getvalue())
        self.assertNotIn("compiler output", self.output.getvalue())
        self.assertNotIn("\033", self.output.getvalue())

    def test_failure_preserves_exit_status_and_never_prints_success(self):
        log = self.root / "failure.log"
        with self.assertRaises(build.StageFailed) as failure:
            self.runner.run(2, 4, "Configure", [sys.executable, "-c", "print('bad config'); exit(7)"], log)
        self.assertEqual(failure.exception.code, 7)
        self.assertIn("bad config", log.read_text())
        self.assertIn("[FAIL] [2/4] Configure", self.output.getvalue())
        self.assertNotIn("[OK]", self.output.getvalue())

    def test_verbose_streams_output_and_retains_log(self):
        self.display.verbose = True
        log = self.root / "verbose.log"
        self.runner.run(1, 1, "Tools", [sys.executable, "-c", "print('download details')"], log)
        self.assertIn("download details", self.output.getvalue())
        self.assertIn("download details", log.read_text())

    def test_failed_build_stops_before_later_stages_and_shows_log_excerpt(self):
        # No bootstrap exists in this isolated project, so stage one must fail.
        program = (
            "from pathlib import Path; import sys; from tools.scripts import build; "
            f"build.ROOT = Path({str(self.root)!r}); "
            "sys.argv = ['build.py', '--config', 'Release', '--plain']; "
            "sys.exit(build.main())"
        )
        result = subprocess.run([sys.executable, "-B", "-c", program],
                                cwd=Path(__file__).resolve().parents[1],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("[FAIL] [1/4]", result.stdout)
        self.assertIn("Full log:", result.stdout)
        self.assertIn("can't open file", result.stdout)
        self.assertNotIn("[2/4]", result.stdout)
        self.assertNotIn("Build complete", result.stdout)

    def test_interrupt_stops_active_process(self):
        real_popen = subprocess.Popen
        processes = []

        def capture(*args, **kwargs):
            process = real_popen(*args, **kwargs)
            processes.append(process)
            return process

        real_sleep = build.time.sleep
        interrupted = False

        def interrupt_once(duration):
            nonlocal interrupted
            if not interrupted:
                interrupted = True
                raise KeyboardInterrupt
            real_sleep(duration)

        with patch.object(build.subprocess, "Popen", side_effect=capture):
            with patch.object(build.time, "sleep", side_effect=interrupt_once):
                with self.assertRaises(KeyboardInterrupt):
                    self.runner.run(1, 1, "Compile", [sys.executable, "-c", "import time; time.sleep(30)"],
                                    self.root / "interrupt.log")
        self.assertIsNotNone(processes[0].poll())
        self.assertIn("[FAIL]", self.output.getvalue())

    def test_no_color_keeps_terminal_status_uncolored(self):
        class Terminal(io.StringIO):
            def isatty(self):
                return True

        output = Terminal()
        with patch.dict(os.environ, {"TERM": "xterm", "NO_COLOR": "1"}):
            display = build.Display(stream=output)
            display.finish(1, 1, "Tools", 0.2, True)
        self.assertNotIn("\033[32m", output.getvalue())
        self.assertIn("Tools", output.getvalue())

    def test_rebuild_resets_only_selected_configuration(self):
        paths = ["out/build/Release/CMakeCache.txt", "out/build/Debug/object.o",
                 "out/tools/tool", "out/deps/source", "out/cache/package", "source/keep"]
        for name in paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("keep")
        build.reset_output(self.root, "Release")
        self.assertFalse((self.root / "out/build/Release").exists())
        for name in paths[1:]:
            self.assertEqual((self.root / name).read_text(), "keep")

    def test_fresh_removes_all_output_but_preserves_source(self):
        output = self.root / "out/tools/cmake"
        output.parent.mkdir(parents=True)
        output.write_text("generated")
        source = self.root / "source/keep"
        source.parent.mkdir()
        source.write_text("source")
        build.reset_output(self.root, "Release", fresh=True)
        self.assertFalse((self.root / "out").exists())
        self.assertEqual(source.read_text(), "source")

    def test_reset_refuses_symbolic_links_and_invalid_configuration(self):
        for index, relative in enumerate(("out", "out/build", "out/build/Release")):
            root = self.root / str(index)
            external = root / "external"
            external.mkdir(parents=True)
            sentinel = external / "keep"
            sentinel.write_text("source")
            link = root / relative
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(external, target_is_directory=True)
            with self.assertRaises(ValueError):
                build.reset_output(root, "Release")
            self.assertEqual(sentinel.read_text(), "source")
            self.assertTrue(link.is_symlink())
        with self.assertRaises(ValueError):
            build.reset_output(self.root, "../../source")

    def test_workspace_lock_rejects_a_second_build(self):
        with build.workspace_lock(self.root):
            with self.assertRaisesRegex(RuntimeError, "Another build is active"):
                with build.workspace_lock(self.root):
                    self.fail("Second build acquired the workspace lock")
        with build.workspace_lock(self.root):
            pass  # The first lock must have been released.


if __name__ == "__main__":
    unittest.main()
