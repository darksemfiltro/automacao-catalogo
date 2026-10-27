"""A direção deve existir antes da composição e impedir o fundo-diagrama fixo."""
import json
import unittest
from build_cenas import plan_scenes, build_elements
from gen_comp import build_html


class ScenePlanTests(unittest.TestCase):
    def fixture(self, texts):
        segments = [{"id": f"s{i}", "chapter": "estrela", "text": text}
                    for i, text in enumerate(texts)]
        timing = {"total": len(texts) * 3.0,
                  "segments": [dict(s, start=i * 3.0, dur=3.0)
                               for i, s in enumerate(segments)]}
        script = {"episode": "Estrelas", "segments": segments,
                  "chapters": [{"id": "estrela", "label": "Estrela",
                                "segments": [s["id"] for s in segments]}]}
        plan = {"theme": "cartoon", "defaults": {},
                "chapters": {"estrela": {"mg": "star_glow"}}, "cenas": {}}
        return plan, timing, {"segments": []}, script

    def test_repeated_subject_varies_without_inventing_diagrams(self):
        args = self.fixture(["A estrela brilha."] * 12)
        shots = plan_scenes(*args)
        self.assertEqual(shots, plan_scenes(*args))
        self.assertGreaterEqual(len({s["tipo"] for s in shots}), 3)
        for a, b in zip(shots, shots[1:]):
            self.assertNotEqual(a["tipo"], b["tipo"])
            self.assertNotEqual(a["entrada"], b["entrada"])
            self.assertAlmostEqual(a["start"] + a["dur"], b["start"])
        self.assertLessEqual(sum(s["recipe"] is not None for s in shots), 1)

    def test_data_variation_keeps_number_and_unit(self):
        args = self.fixture(["A temperatura chega a 2500 K."] * 4)
        shots = plan_scenes(*args)
        self.assertEqual([s["tipo"] for s in shots], ["dados", "dado_texto"] * 2)
        elements = build_elements(*args, scene_plan=shots)
        self.assertTrue(any(e["tipo"] == "callout" and "2500 K" in e["texto"]
                            for e in elements))
        self.assertFalse(any(e.get("modo") == "full" for e in elements))

    def test_renderer_has_only_scoped_backgrounds_and_no_generic_sweep(self):
        args = self.fixture(["A estrela brilha."] * 6)
        shots = plan_scenes(*args)
        ep = {"total": 18, "episode": "Estrelas", "scene_plan": shots,
              "elements": build_elements(*args, scene_plan=shots)}
        result = build_html(ep, "cartoon")
        html = result[0] if isinstance(result, tuple) else result
        self.assertEqual(html.count('data-background='), len(shots))
        self.assertNotIn('class="mg-sweep"', html)
        self.assertNotIn('class="mg-sheen"', html)
        self.assertNotIn('id="tw0"', html)

    def test_author_objects_and_actions_are_preserved(self):
        args = self.fixture(["A casa desaba."])
        args[0]["cenas"]["s0"] = [{"tipo": "ilustra", "id": "house", "effect": "collapse"}]
        elements = build_elements(*args)
        self.assertTrue(any(e.get("id") == "house" and e.get("effect") == "collapse"
                            for e in elements))

    def test_author_captions_do_not_force_identical_scenes(self):
        args = self.fixture(["A estrela brilha."] * 8)
        args[0]["cenas"] = {f"s{i}": [{"tipo": "frase", "texto": "ESTRELA"}]
                             for i in range(8)}
        shots = plan_scenes(*args)
        self.assertTrue(all(s["autoral"] for s in shots))
        self.assertTrue(all(a["tipo"] != b["tipo"] for a, b in zip(shots, shots[1:])))

    def test_comparison_circles_fit_their_viewbox(self):
        import mg
        import xml.etree.ElementTree as ET
        for count in (2, 4, 8):
            spec = mg.build("size_compare", "test", {"itens": [
                {"escala": (i + 1) / count, "rotulo": str(i)} for i in range(count)]})
            svg = ET.fromstring(f'<svg>{spec["inner"]}</svg>')
            for circle in svg.findall('.//circle'):
                x, r = float(circle.attrib['cx']), float(circle.attrib['r'])
                self.assertGreaterEqual(x - r, 0)
                self.assertLessEqual(x + r, spec['vb'][0])

    def test_gate_rejects_regression_to_repeated_direction(self):
        from gauntlet import check
        args = self.fixture(["A estrela brilha."] * 3)
        shots = plan_scenes(*args)
        ep = {"total": 9, "scene_plan": shots, "elements": build_elements(*args, scene_plan=shots)}
        self.assertFalse(any(code.startswith("plano_") for code, _, _ in check(ep)))
        shots[1]["tipo"] = shots[0]["tipo"]
        shots[1]["start"] += 0.5
        codes = {code for code, _, _ in check(ep)}
        self.assertIn("plano_repetido", codes)
        self.assertIn("plano_intervalo", codes)


if __name__ == "__main__":
    unittest.main()
