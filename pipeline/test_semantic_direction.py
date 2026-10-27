"""Regressões editoriais para a direção visual automática do Catálogo."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_cenas import semantic_objects


def selected(text, words, topic="nature", scene="wind_field"):
    pairs = [(word, 0.3 + i * 0.45) for i, word in enumerate(words)]
    return semantic_objects(text, pairs, topic, scene, 0.0, max(3.0, len(pairs)))


class SemanticDirectionTests(unittest.TestCase):
    def test_destruction_has_visible_target_and_action(self):
        els = selected("destruiu tudo", ["destruiu", "tudo"], scene="vortex")
        self.assertIn(("house", "collapse"),
                      [(e["id"], e.get("effect")) for e in els])

    def test_heat_and_flood_are_concrete(self):
        heat = selected("calor extremo", ["calor", "extremo"], scene="wildfire")
        flood = selected("a água invade casas", ["a", "água", "invade", "casas"],
                         scene="water_rise")
        self.assertIn("flame", [e["id"] for e in heat])
        self.assertIn(("house", "flood"),
                      [(e["id"], e.get("effect")) for e in flood])

    def test_context_blocks_false_friends(self):
        fire = selected("o fogo se espalha", ["o", "fogo", "se", "espalha"],
                        scene="wildfire")
        sight = selected("derruba a visibilidade", ["derruba", "a", "visibilidade"],
                         scene="snowstorm")
        self.assertNotIn("prism", [e["id"] for e in fire])
        self.assertFalse(any(e.get("effect") == "collapse" for e in sight))

    def test_compound_noun_beats_color_adjective(self):
        star = selected("anã vermelha", ["anã", "vermelha"],
                        topic="astro", scene="star_glow")
        self.assertEqual("red_dwarf", star[0]["id"])
        self.assertNotIn("red_giant", [e["id"] for e in star])

    def test_rotation_is_an_action_not_a_gear_icon(self):
        wind = selected("o tornado gira", ["o", "tornado", "gira"], scene="vortex")
        self.assertIn(("tornado", "spin"),
                      [(e["id"], e.get("effect")) for e in wind])


if __name__ == "__main__":
    unittest.main()
