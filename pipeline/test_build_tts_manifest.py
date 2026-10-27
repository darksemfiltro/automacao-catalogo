"""Testes do contrato público do gerador de manifestos de voz."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from build_tts_manifest import BASE_SEED, main


class BuildTtsManifestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "meu projeto"
        self.project.mkdir()
        self.phonetic = self.project / "roteiro_fonetico_v1.json"
        self.phonetic.write_text(json.dumps({"segments": [
            {"id": "ab01", "text": "Primeira frase.", "attempt": 1},
            {"id": "ab02", "text": "Segunda frase.", "attempt": 3},
            {"id": "ab03@2", "text": "Frase legada."},
        ]}), encoding="utf-8")
        self.audio = Path(self.temp.name) / "voz.wav"
        self.audio.write_bytes(b"audio de teste")

    def test_sidecar_text_and_attempts_produce_stable_logical_ids(self):
        self.audio.with_suffix(".txt").write_text("  Minha voz de teste.  \n", encoding="utf-8")

        with patch.dict("os.environ", {"CATALOGO_REF_AUDIO": str(self.audio)}):
            dest = main(self.project, self.phonetic.name)

        manifest = json.loads(dest.read_text(encoding="utf-8"))
        self.assertEqual(str(self.audio.resolve()), manifest["ref_audio"])
        self.assertEqual("Minha voz de teste.", manifest["ref_text"])
        self.assertEqual(str(self.project / "assets" / "audio" / "v1"), manifest["output_dir"])
        self.assertEqual(["ab01", "ab02", "ab03"], [s["id"] for s in manifest["segments"]])
        self.assertEqual([BASE_SEED, BASE_SEED + 1002, BASE_SEED + 2001],
                         [s["seed"] for s in manifest["segments"]])
        self.assertEqual(str(self.project / "assets" / "audio" / "v1" / "ab03.wav"),
                         manifest["segments"][2]["output"])

    def test_cli_accepts_explicit_text_speed_and_logical_only_id(self):
        result = subprocess.run([
            sys.executable, str(Path(__file__).with_name("build_tts_manifest.py")),
            str(self.project), self.phonetic.name, "v2", "--ref-audio", str(self.audio),
            "--ref-text", "Uma referência.", "--only", "ab02", "--speed", "1.15",
        ], text=True, capture_output=True)

        self.assertEqual(0, result.returncode, result.stderr)
        manifest = json.loads((self.project / "tts_manifest_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(["ab02"], [s["id"] for s in manifest["segments"]])
        self.assertEqual(1.15, manifest["segments"][0]["speed"])
        self.assertEqual(BASE_SEED + 1002, manifest["segments"][0]["seed"])

    def test_sem_referencia_omite_voz_para_api_ou_comando_local(self):
        dest = main(self.project, self.phonetic.name, sem_referencia=True)

        manifest = json.loads(dest.read_text(encoding="utf-8"))
        self.assertNotIn("ref_audio", manifest)
        self.assertNotIn("ref_text", manifest)
        self.assertEqual(["ab01", "ab02", "ab03"], [s["id"] for s in manifest["segments"]])

    def test_sem_referencia_nao_combina_com_referencia(self):
        with self.assertRaises(ValueError):
            main(self.project, self.phonetic.name, ref_audio=str(self.audio), sem_referencia=True)

    def test_legacy_positional_only_and_text_file(self):
        text_file = Path(self.temp.name) / "texto.txt"
        text_file.write_text("Texto em arquivo.", encoding="utf-8")
        result = subprocess.run([
            sys.executable, str(Path(__file__).with_name("build_tts_manifest.py")),
            str(self.project), self.phonetic.name, "v1", "ab03",
            "--ref-audio", str(self.audio), "--ref-text-file", str(text_file),
        ], text=True, capture_output=True)

        self.assertEqual(0, result.returncode, result.stderr)
        manifest = json.loads((self.project / "tts_manifest_v1.json").read_text(encoding="utf-8"))
        self.assertEqual("Texto em arquivo.", manifest["ref_text"])
        self.assertEqual(["ab03"], [s["id"] for s in manifest["segments"]])

    def test_missing_reference_fails_without_writing_manifest(self):
        with patch.dict("os.environ", {"CATALOGO_REF_AUDIO": ""}):
            result = subprocess.run([
                sys.executable, str(Path(__file__).with_name("build_tts_manifest.py")),
                str(self.project), self.phonetic.name,
            ], text=True, capture_output=True)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("Informe --ref-audio", result.stderr)
        self.assertFalse((self.project / "tts_manifest_v1.json").exists())

    def test_missing_transcript_fails_without_writing_manifest(self):
        result = subprocess.run([
            sys.executable, str(Path(__file__).with_name("build_tts_manifest.py")),
            str(self.project), self.phonetic.name, "--ref-audio", str(self.audio),
        ], text=True, capture_output=True)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("Transcrição de referência não encontrada", result.stderr)
        self.assertFalse((self.project / "tts_manifest_v1.json").exists())


if __name__ == "__main__":
    unittest.main()
