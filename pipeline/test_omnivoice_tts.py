"""Migração de voz: subprocesso/cliente simulados, sem rede ou GPU."""
import contextlib
import copy
import io
import json
import os
import sys
import tempfile
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import omnivoice_tts as tts


class VoiceMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runner = self.root / "run_tts_batch_compat.py"
        self.runner.write_text("# cliente simulado", encoding="utf-8")
        self.ref = self.root / "referencia.wav"
        self.ref.write_bytes(b"referencia de teste")
        self.output = self.root / "s01.wav"
        self.manifest = self.root / "manifest.json"
        self.data = {
            "ref_audio": str(self.ref), "ref_text": "Referência já transcrita.",
            "language": "Portuguese", "output_dir": str(self.root),
            "segments": [{"id": "s01", "text": " Uma frase. ", "output": str(self.output),
                          "language": "Portuguese", "speed": 1.0, "seed": 90000,
                          "gap_after": 0.0}],
        }
        self.save()
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {}, clear=True).start()
        patch.object(tts, "voice_config", return_value={
            "modo": "central", "central_runner": str(self.runner)}).start()

    def save(self):
        self.manifest.write_text(json.dumps(self.data), encoding="utf-8")

    def invoke(self, *args):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            tts.main([str(self.manifest), *args])

    def write_wav(self):
        with wave.open(str(self.output), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24000)
            wav.writeframes(b"\0\0" * 24)

    def test_central_dispatches_unchanged_manifest_to_simulated_client(self):
        original_bytes = self.manifest.read_bytes()
        client = SimpleNamespace(sintetizar=Mock(return_value={"ok": True}))
        def run(command, **kwargs):
            self.assertEqual(str(self.runner), command[1])
            sent = json.loads(Path(command[command.index("--manifest") + 1]).read_text(encoding="utf-8"))
            client.sintetizar(sent)
            self.write_wav()
        with patch.object(tts.subprocess, "run", side_effect=run) as process:
            self.invoke("--device", "cuda")
        self.assertEqual(1, process.call_count)
        self.assertEqual(str(Path(sys.executable)), process.call_args.args[0][0])
        self.assertEqual(["--device", "cuda"], process.call_args.args[0][-2:])
        client.sintetizar.assert_called_once_with(self.data)
        self.assertEqual(original_bytes, self.manifest.read_bytes())

    def test_check_never_launches_subprocess_in_either_mode(self):
        with patch.object(tts.subprocess, "run") as process:
            self.invoke("--check")
            self.invoke("--modo", "direto", "--check")
        process.assert_not_called()
        self.assertFalse(self.output.exists())

    def test_explicit_direct_home_keeps_original_runner(self):
        home = self.root / "omnivoice"
        interpreter = home / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        interpreter.parent.mkdir(parents=True)
        interpreter.touch()
        (home / "run_tts_batch.py").touch()
        def run(command, **kwargs):
            if "--manifest" in command:
                self.write_wav()
        with patch.object(tts.subprocess, "run", side_effect=run) as process:
            self.invoke("--modo", "direto", "--home", str(home))
        self.assertEqual(2, process.call_count)
        self.assertIn("from omnivoice.models.omnivoice import OmniVoice", process.call_args_list[0].args[0][2])
        self.assertEqual(str(home / "run_tts_batch.py"), process.call_args.args[0][1])
        self.assertEqual(str(interpreter), process.call_args.args[0][0])

    def test_explicit_direct_without_home_keeps_portable_worker(self):
        with patch.object(tts.subprocess, "run", side_effect=lambda *a, **kw: self.write_wav()) as process:
            self.invoke("--modo", "direto")
        self.assertEqual(str(Path(tts.__file__).with_name("omnivoice_worker.py")), process.call_args.args[0][1])

    def test_existing_output_is_preserved(self):
        self.output.write_bytes(b"WAV existente")
        with patch.object(tts.subprocess, "run") as process, self.assertRaises(SystemExit):
            self.invoke()
        process.assert_not_called()
        self.assertEqual(b"WAV existente", self.output.read_bytes())

    def test_central_failure_does_not_automatically_run_direct(self):
        error = tts.subprocess.CalledProcessError(1, ["central"])
        with patch.object(tts.subprocess, "run", side_effect=error) as process:
            with self.assertRaises(tts.subprocess.CalledProcessError):
                self.invoke()
        self.assertEqual(1, process.call_count)

    def test_missing_transcript_stops_before_subprocess(self):
        self.data.pop("ref_text")
        self.save()
        with patch.object(tts.subprocess, "run") as process, self.assertRaisesRegex(ValueError, "Transcrição"):
            self.invoke("--check")
        process.assert_not_called()

    def test_sibling_transcript_accepts_bom_without_changing_manifest(self):
        self.data.pop("ref_text")
        self.ref.with_suffix(".txt").write_text("  Transcrição.  ", encoding="utf-8-sig")
        self.save()
        original = self.manifest.read_bytes()
        self.invoke("--check")
        self.assertEqual(original, self.manifest.read_bytes())

    def test_blank_sibling_transcript_rejected(self):
        self.data.pop("ref_text")
        self.ref.with_suffix(".txt").write_text(" \n ", encoding="utf-8")
        self.save()
        with self.assertRaises(ValueError):
            self.invoke("--check")

    def test_segment_null_overrides_global_transcript(self):
        data = copy.deepcopy(self.data)
        data["segments"][0]["ref_text"] = None
        with self.assertRaises(ValueError):
            tts.validate_ref_text(data)

    def test_environment_and_cli_select_explicit_modes(self):
        with patch.dict(os.environ, {"CATALOGO_VOZ_MODO": "direto",
                                     "CATALOGO_CENTRAL_RUNNER": str(self.runner)}):
            self.invoke("--check")
            self.invoke("--modo", "central", "--check")
        with patch.dict(os.environ, {"CATALOGO_VOZ_MODO": "invalido"}), self.assertRaises(SystemExit):
            self.invoke("--check")

    def test_config_is_operational_only(self):
        config = self.root / "voz.json"
        expected = {"modo": "central", "central_runner": str(self.runner)}
        config.write_text(json.dumps(expected), encoding="utf-8")
        # Use a função real: o patch de setUp só controla os defaults da CLI.
        patch.stopall()
        self.assertEqual(expected, tts.voice_config(config))
        self.assertEqual({}, tts.voice_config(self.root / "ausente.json"))


if __name__ == "__main__":
    unittest.main()
