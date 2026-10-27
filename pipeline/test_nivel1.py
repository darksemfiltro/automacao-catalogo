"""Gates devem recusar produção desatualizada; testes não baixam modelos."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from analisar_video import silence_ranges, analyze
from omnivoice_tts import validate_manifest
from referencias import load_references, validate_tokens
from transcrever import transcribe
from workflow import (create_storyboard, record_build, review, validate_review,
                      validate_episode, write)


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "producao"
        self.project.mkdir()
        self.comp = self.project / "hyperframes"
        self.comp.mkdir()
        self.ep = {"total": 2, "episode": "Teste <seguro>", "elements": [], "scene_plan": [
            {"id": "c1", "segment": "s1", "tipo": "objeto", "start": 0,
             "dur": 2, "motivo": "Objeto da fala"}]}
        write(self.project / "episode.json", self.ep)
        (self.comp / "index.html").write_text("composição", encoding="utf-8")
        self.frame = self.project / "frame.png"
        self.frame.write_bytes(b"fixture")

    def prepare(self, seconds=None):
        create_storyboard(self.project)
        record_build(self.project, self.comp, "episode.json", "cartoon", seconds)
        review(self.project, self.comp, "Teste automatizado", "Fixture, não aprovação editorial", [self.frame])

    def test_valid_review_and_html_escape(self):
        self.prepare()
        validate_review(self.project, self.comp)
        self.assertIn("&lt;seguro&gt;", (self.project / "storyboard.html").read_text(encoding="utf-8"))

    def test_missing_review_blocks(self):
        create_storyboard(self.project)
        record_build(self.project, self.comp, "episode.json", "cartoon", None)
        with self.assertRaises(FileNotFoundError):
            validate_review(self.project, self.comp)

    def test_edited_spec_invalidates_review(self):
        self.prepare()
        self.ep["episode"] = "Novo título"
        write(self.project / "episode.json", self.ep)
        with self.assertRaisesRegex(ValueError, "Storyboard desatualizado"):
            validate_review(self.project, self.comp)

    def test_edited_composition_invalidates_review(self):
        self.prepare()
        (self.comp / "index.html").write_text("alterado", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Composição alterada"):
            validate_review(self.project, self.comp)

    def test_new_audio_invalidates_review(self):
        self.prepare()
        audio = self.project / "assets" / "audio"
        audio.mkdir(parents=True)
        (audio / "new.wav").write_bytes(b"new")
        with self.assertRaisesRegex(ValueError, "Storyboard desatualizado"):
            validate_review(self.project, self.comp)

    def test_partial_composition_cannot_be_final(self):
        with self.assertRaisesRegex(ValueError, "sem --seconds"):
            self.prepare(seconds=1)

    def test_changed_frame_invalidates_review(self):
        self.prepare()
        self.frame.write_bytes(b"edited")
        with self.assertRaisesRegex(ValueError, "Quadros"):
            validate_review(self.project, self.comp)

    def test_gap_overlap_unknown_scene_and_nan_rejected(self):
        for key, value in [("start", .3), ("dur", -1), ("dur", float("nan")), ("tipo", "split")]:
            ep = copy.deepcopy(self.ep)
            ep["scene_plan"][0][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_episode(ep)

    def test_storyboard_cannot_silently_change_scenes(self):
        self.prepare()
        path = self.project / "storyboard.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["scenes"][0]["tipo"] = "dados"
        write(path, data)
        with self.assertRaisesRegex(ValueError, "Storyboard desatualizado"):
            validate_review(self.project, self.comp)

    def test_references_are_inputs_and_tokens_apply(self):
        folder = self.project / "referencias"
        folder.mkdir()
        write(folder / "manifest.json", {"schema_version": 1, "references": [],
                                         "tokens": {"title_color": "#abcdef"}})
        self.prepare()
        self.assertEqual(load_references(folder)["title_color"], "#abcdef")
        write(folder / "manifest.json", {"schema_version": 1, "tokens": {}})
        with self.assertRaises(ValueError):
            validate_review(self.project, self.comp)

    def test_reference_cannot_escape_folder(self):
        folder = self.project / "referencias"
        folder.mkdir()
        write(folder / "manifest.json", {"schema_version": 1, "references": [
            {"file": "../episode.json", "source": "x", "license": "MIT", "observations": "x"}]})
        with self.assertRaises(ValueError):
            load_references(folder)


class MediaTests(unittest.TestCase):
    def test_silence_trailing_and_multiple(self):
        log = "silence_start: 0\nsilence_end: 1.25\nsilence_start: 3"
        result = silence_ranges(log, 5)
        self.assertEqual([(r["start"], r["end"]) for r in result], [(0, 1.25), (3, 5)])
        self.assertTrue(all(r["action"] == "review_only" for r in result))

    def test_invalid_sampling_never_invokes_ffmpeg(self):
        with patch("analisar_video.subprocess.run") as run:
            for value in [0, -1, float("nan"), float("inf")]:
                with self.assertRaises(ValueError):
                    analyze("absent", "out", value)
            run.assert_not_called()

    def test_asr_consumes_generator_and_keeps_word_ends(self):
        class Model:
            def transcribe(self, *args, **kwargs):
                assert kwargs["word_timestamps"] is True
                return iter([SimpleNamespace(words=[SimpleNamespace(word=" Olá", start=.2,
                            end=.7, probability=.9)])]), SimpleNamespace(language="pt", duration=1)
        result = transcribe(Model(), Path("fake.wav"), "pt")
        self.assertEqual(result["words"][0]["t_end"], .7)
        self.assertEqual(result["words"][0]["w"], "Olá")
        self.assertNotIn("aligned", result["words"][0])

    def test_empty_transcription_rejected(self):
        class Model:
            def transcribe(self, *args, **kwargs):
                return iter([]), SimpleNamespace(language="pt", duration=1)
        with self.assertRaises(ValueError):
            transcribe(Model(), Path("fake.wav"), "pt")

    def test_css_injection_and_invalid_sizes_rejected(self):
        for tokens in [{"title_color": "red;display:none"}, {"fonts": "url(x)"},
                       {"title_size": 200}, {"title_size": float("nan")}]:
            with self.subTest(tokens=tokens), self.assertRaises(ValueError):
                validate_tokens(tokens)

    def test_renderer_consumes_reference_tokens(self):
        from gen_comp import build_html
        ep = {"total": 2, "visual_tokens": {"callout_color": "#abcdef"}, "elements": [
            {"tipo": "callout", "texto": "DADO", "start": 0, "dur": 2, "pos": "dir"}]}
        self.assertIn("#abcdef", build_html(ep, "cartoon"))

    def test_render_stops_before_subprocess_without_storyboard(self):
        import render_final
        with TemporaryDirectory() as tmp, patch("sys.argv", ["render_final.py", tmp]):
            with patch("render_final.subprocess.run") as run:
                with self.assertRaises(FileNotFoundError):
                    render_final.main()
                run.assert_not_called()

    def test_tts_duplicate_outputs_rejected(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            segments = [{"id": sid, "text": "Teste", "output": str(Path(tmp) / "one.wav")}
                        for sid in ["a", "b"]]
            write(path, {"segments": segments})
            with self.assertRaisesRegex(ValueError, "Saída duplicada"):
                validate_manifest(path)

    def test_tts_cannot_overwrite_reference(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "manifest.json"
            ref = Path(tmp) / "voice.wav"
            ref.write_bytes(b"ref")
            write(path, {"ref_audio": str(ref), "segments": [
                {"id": "a", "text": "Teste", "output": str(ref)}]})
            with self.assertRaises(ValueError):
                validate_manifest(path)


if __name__ == "__main__":
    unittest.main()
