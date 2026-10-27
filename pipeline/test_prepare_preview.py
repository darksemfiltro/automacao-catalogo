"""Regression tests for safe preview output paths."""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import prepare_preview


class PreparePreviewTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.project = Path(self.workspace.name) / "episode"
        self.source = self.project / "hyperframes"
        self.source.mkdir(parents=True)
        (self.source / "index.html").write_text(
            '<div class="clip" id="root" data-duration="90.000"></div>',
            encoding="utf-8",
        )
        (self.source / "index.motion.json").write_text(
            json.dumps({"duration": 90}), encoding="utf-8"
        )

    def run_preview(self, *args):
        argv = ["prepare_preview.py", "--project", str(self.project), *args]
        output = io.StringIO()
        with (patch.object(sys, "argv", argv),
              contextlib.redirect_stdout(output),
              contextlib.redirect_stderr(io.StringIO())):
            prepare_preview.main()
        return Path(output.getvalue().strip())

    def test_default_output_is_outside_source_and_bounded(self):
        destination = self.run_preview("--seconds", "12")
        self.addCleanup(shutil.rmtree, destination)
        self.assertNotIn(self.source.resolve(), destination.resolve().parents)
        self.assertIn('data-duration="12.000"',
                      (destination / "index.html").read_text(encoding="utf-8"))
        self.assertEqual(12, json.loads(
            (destination / "index.motion.json").read_text(encoding="utf-8")
        )["duration"])

    def test_nested_destination_is_rejected_without_deleting_it(self):
        destination = self.source / "_preview60"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("user data", encoding="utf-8")
        with self.assertRaises(SystemExit) as error:
            self.run_preview("--out-dir", str(destination))
        self.assertEqual(2, error.exception.code)
        self.assertEqual("user data", marker.read_text(encoding="utf-8"))

    def test_ancestor_destination_is_rejected_without_deleting_project(self):
        with self.assertRaises(SystemExit) as error:
            self.run_preview("--out-dir", str(self.project))
        self.assertEqual(2, error.exception.code)
        self.assertTrue((self.source / "index.html").exists())

    def test_existing_sibling_destination_is_preserved(self):
        destination = self.project / "preview"
        destination.mkdir()
        marker = destination / "keep.txt"
        marker.write_text("user data", encoding="utf-8")
        with self.assertRaises(SystemExit) as error:
            self.run_preview("--out-dir", str(destination))
        self.assertEqual(2, error.exception.code)
        self.assertEqual("user data", marker.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
