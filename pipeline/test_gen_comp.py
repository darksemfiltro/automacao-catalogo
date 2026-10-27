"""Regressões do empacotamento de mídia na composição pública."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_comp


class GenCompMediaTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.spec = {
            "theme": "cartoon", "total": 3.0, "episode": "Demonstração",
            "version": "v2", "chapters": [],
            "elements": [{"tipo": "sfx", "nome": "ping", "start": 1.0}],
        }
        (self.project / "episode.json").write_text(
            json.dumps(self.spec), encoding="utf-8")

    def generate(self):
        args = ["gen_comp.py", str(self.project), "--out-dir", "demo"]
        with mock.patch.object(sys, "argv", args):
            gen_comp.main()
        return self.project / "demo" / "index.html"

    def test_missing_local_sfx_is_omitted(self):
        sfx = self.project / "assets" / "sfx"
        sfx.mkdir(parents=True)
        (sfx / "manifest.json").write_text(
            json.dumps({"ping": {"file": "ping.mp3", "duration": 1.0}}),
            encoding="utf-8")

        html = self.generate().read_text(encoding="utf-8")

        self.assertNotIn('id="sfx', html)
        self.assertFalse((self.project / "demo" / "assets" / "sfx" / "ping.mp3").exists())

    def test_spec_version_selects_matching_audio(self):
        audio = self.project / "assets" / "audio"
        audio.mkdir(parents=True)
        (audio / "narration_v1.m4a").write_bytes(b"wrong version")
        (audio / "narration_v2.m4a").write_bytes(b"right version")

        html = self.generate().read_text(encoding="utf-8")

        self.assertIn('src="assets/audio/narration_v2.m4a"', html)
        self.assertEqual(
            b"right version",
            (self.project / "demo" / "assets" / "audio" / "narration_v2.m4a").read_bytes(),
        )
        self.assertFalse((self.project / "demo" / "assets" / "audio" / "narration_v1.m4a").exists())

    def test_legacy_spec_with_multiple_versions_fails(self):
        self.spec.pop("version")
        (self.project / "episode.json").write_text(
            json.dumps(self.spec), encoding="utf-8")
        audio = self.project / "assets" / "audio"
        audio.mkdir(parents=True)
        (audio / "narration_v1.m4a").write_bytes(b"v1")
        (audio / "narration_v2.m4a").write_bytes(b"v2")

        with self.assertRaisesRegex(ValueError, "várias narrações"):
            self.generate()

    def test_motion_loop_puts_options_in_gsap_destination_vars(self):
        js = gen_comp.anim_js(
            "#wind", "mg_loop", 1.25, 5.0,
            {"frm": {"x": 0}, "to": {"x": 10}, "cycle": 2.0, "yoyo": True},
        )
        prefix = 'tl.fromTo("#wind",'
        self.assertTrue(js.startswith(prefix))
        body = js[len(prefix):-2]
        decoder = json.JSONDecoder()
        source, offset = decoder.raw_decode(body)
        self.assertEqual({"x": 0}, source)
        self.assertEqual(",", body[offset])
        destination, consumed = decoder.raw_decode(body[offset + 1:])
        self.assertEqual(",1.25", body[offset + 1 + consumed:])
        self.assertEqual(2.0, destination["duration"])
        self.assertEqual(1, destination["repeat"])
        self.assertTrue(destination["yoyo"])
        self.assertFalse(destination["immediateRender"])

    def test_empty_episode_does_not_invent_a_space_background(self):
        html = gen_comp.build_html(
            {"total": 10.0, "episode": "Teste", "elements": []}, "cartoon"
        )
        self.assertNotIn('id="tw0"', html)
        self.assertNotIn('duration:3.00,ease:"sine.out"', html)

    def test_long_episode_motion_gate_accounts_for_sample_cap(self):
        self.spec["total"] = 760.73
        (self.project / "episode.json").write_text(
            json.dumps(self.spec), encoding="utf-8"
        )
        self.generate()
        sidecar = json.loads(
            (self.project / "demo" / "index.motion.json").read_text(encoding="utf-8")
        )
        self.assertNotIn("maxStaticSec", sidecar)
        moving = next(a for a in sidecar["assertions"] if a["kind"] == "keepsMoving")
        self.assertGreater(moving["maxStaticSec"], 760.73 / 299)
        self.assertLess(moving["maxStaticSec"], 2.6)
        self.assertEqual(2.5, gen_comp.motion_static_limit(60.0))

    def test_short_demo_omits_later_clips_and_trims_crossing_clip(self):
        episode = {"total": 20.0, "elements": [
            {"tipo": "frase", "start": 8.0, "dur": 6.0, "texto": "primeiro"},
            {"tipo": "frase", "start": 12.0, "dur": 2.0, "texto": "depois"},
        ]}

        short = gen_comp.bounded_episode(episode, 10.0)

        self.assertEqual(10.0, short["total"])
        self.assertEqual(1, len(short["elements"]))
        self.assertEqual(2.0, short["elements"][0]["dur"])
        self.assertEqual(6.0, episode["elements"][0]["dur"])


if __name__ == "__main__":
    unittest.main()
