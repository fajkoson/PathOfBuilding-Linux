import io
from pathlib import Path
import sys
import tempfile
import unittest

from tools.scripts.build import Display
from tools.scripts.run import launch


class RunUiTests(unittest.TestCase):
    def run_application(self, script, verbose=False):
        root = Path(__file__).resolve().parents[1] / "out/tests"
        root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root) as directory:
            log = Path(directory) / "runtime.log"
            stream = io.StringIO()
            display = Display(plain=True, verbose=verbose, stream=stream)
            code = launch([sys.executable, "-c", script], "Release", display, log)
            return code, stream.getvalue(), log.read_text()

    def test_startup_stages_and_log(self):
        messages = "Running script...\nRenderer initialised in 42 msec.\nStartup time: 100 ms\nWarning: optional asset\nRares loaded"
        code, output, log = self.run_application(f"print({messages!r})")
        self.assertEqual(code, 0)
        self.assertIn("[OK] [4/4] Load item data", output)
        self.assertIn("Application ready", output)
        self.assertIn("Startup warnings: 1", output)
        self.assertNotIn("Warning: optional asset", output)
        self.assertIn("Warning: optional asset", log)
        self.assertNotIn("\033", output)

    def test_failed_startup_shows_error_and_no_ready_message(self):
        code, output, log = self.run_application('print("graphics failure"); exit(7)')
        self.assertEqual(code, 7)
        self.assertIn("[FAIL]", output)
        self.assertIn("graphics failure", output)
        self.assertNotIn("Application ready", output)

    def test_verbose_streams_raw_output(self):
        code, output, log = self.run_application('print("native diagnostic")', verbose=True)
        self.assertEqual(code, 0)
        self.assertIn("native diagnostic", output)

    def test_lua_error_is_visible_even_on_zero_exit(self):
        code, output, log = self.run_application('print("--- SCRIPT ERROR ---\\nBad Lua")')
        self.assertIn("Runtime error reported", output)
        self.assertIn("Bad Lua", output)
