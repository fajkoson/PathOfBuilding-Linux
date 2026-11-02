import hashlib
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from tools.scripts import bootstrap


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1] / "out/tests"
        root.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(dir=root)
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tools = self.root / "tools"
        self.downloads = self.root / "downloads"
        self.logs = self.root / "logs"
        for directory in (self.tools, self.downloads, self.logs):
            directory.mkdir()

    def test_installed_tool_can_be_reused_without_archive_or_network(self):
        archive = self.downloads / "ninja.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("ninja", "#!/bin/sh\nexit 0\n")
        entry = dict(version="test", archive=archive.name, url="https://invalid.test/ninja",
                     sha256=bootstrap.digest(archive), format="zip", build="binary",
                     executables={"ninja": "ninja"})
        with patch.object(bootstrap.subprocess, "run", side_effect=AssertionError("network used")):
            bootstrap.install("ninja", entry, self.tools, self.downloads, self.logs)
            archive.unlink()
            bootstrap.install("ninja", entry, self.tools, self.downloads, self.logs)
        executable = self.tools / "bin/ninja"
        self.assertTrue(executable.is_symlink())
        self.assertEqual(subprocess.run([executable], check=False).returncode, 0)

    def test_corrupt_cache_is_replaced_only_after_checksum_validation(self):
        expected = b"verified archive bytes"
        archive = self.downloads / "tool.zip"
        archive.write_bytes(b"corrupt cached bytes")
        entry = dict(archive=archive.name, url="https://invalid.test/tool",
                     sha256=hashlib.sha256(expected).hexdigest())

        def fetched(arguments, **kwargs):
            Path(arguments[arguments.index("--output") + 1]).write_bytes(expected)
            return subprocess.CompletedProcess(arguments, 0)

        with patch.object(bootstrap.subprocess, "run", side_effect=fetched):
            bootstrap.download(entry, self.downloads)
        self.assertEqual(archive.read_bytes(), expected)

        entry["sha256"] = "0" * 64
        with patch.object(bootstrap.subprocess, "run", side_effect=fetched):
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                bootstrap.download(entry, self.downloads)
        self.assertEqual(archive.read_bytes(), expected)
        self.assertFalse(archive.with_suffix(".zip.part").exists())

    def test_zip_cannot_write_outside_extraction_directory(self):
        archive = self.downloads / "unsafe.zip"
        with zipfile.ZipFile(archive, "w") as output:
            output.writestr("../escaped", "outside")
        destination = self.root / "unpacked"
        destination.mkdir()
        with self.assertRaisesRegex(RuntimeError, "Unsafe ZIP member"):
            bootstrap.extract(archive, destination, "zip")
        self.assertFalse((self.root / "escaped").exists())


if __name__ == "__main__":
    unittest.main()
