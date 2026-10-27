"""Tests for audio timing and cross-platform FFmpeg measurement."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import assemble


class AssembleTests(unittest.TestCase):
    def test_ebur128_uses_portable_null_output(self):
        stderr = "\n  I: -16.0 LUFS\n  LRA: 2.5 LU\n  Peak: -1.2 dBFS\n"
        with patch.object(assemble.subprocess, "run",
                          return_value=SimpleNamespace(stderr=stderr)) as run:
            result = assemble.ebur128_measure(Path("narration.wav"))
        self.assertEqual(["-f", "null", "-"], run.call_args.args[0][-3:])
        self.assertEqual(-16.0, result["integrated_lufs"])

    def test_total_matches_written_narration_duration(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "segments_v1.json").write_text('{"segments": []}', encoding="utf-8")
            (project / "tts_result_v1.json").write_text('{"segments": []}', encoding="utf-8")
            narration = project / "narration.wav"
            timing = [{"id": "linha01", "start": 0.5, "dur": 2.2}]
            argv = ["assemble.py", "--project", str(project), "--version", "v1"]
            with (patch.object(sys, "argv", argv),
                  patch.object(assemble, "build_voice", return_value=(timing, [], narration)),
                  patch.object(assemble.sf, "info", return_value=SimpleNamespace(duration=3.91)),
                  patch.object(assemble, "find_bed", return_value=None),
                  patch.object(assemble, "ebur128_measure", return_value={}),
                  contextlib.redirect_stdout(io.StringIO())):
                assemble.main()
            result = json.loads((project / "timing_v1.json").read_text(encoding="utf-8"))
            self.assertEqual(3.91, result["total"])


if __name__ == "__main__":
    unittest.main()
