"""Keep rerender attempts separate from stable segment IDs."""

import tempfile
import unittest
from pathlib import Path

from parse_roteiro import parse, validate


class RoteiroIdTests(unittest.TestCase):
    def parse_text(self, text):
        with tempfile.TemporaryDirectory() as directory:
            roteiro = Path(directory) / "roteiro.md"
            roteiro.write_text(text, encoding="utf-8")
            return parse(str(roteiro))

    def test_attempt_suffix_does_not_change_segment_or_chapter_ids(self):
        data = self.parse_text(
            "# Exemplo\n## Capítulo\n"
            "- `linha01@2` [gap:0.30] Primeira frase.\n"
            "- `linha02` Segunda frase.\n"
        )
        self.assertEqual(["linha01", "linha02"],
                         [segment["id"] for segment in data["segments"]])
        self.assertEqual([2, 1],
                         [segment["attempt"] for segment in data["segments"]])
        self.assertEqual(["linha01", "linha02"], data["chapters"][0]["segments"])

    def test_duplicate_logical_id_is_reported(self):
        data = self.parse_text(
            "# Exemplo\n## Capítulo\n"
            "- `linha01` Primeira frase.\n"
            "- `linha01@2` Segunda frase.\n"
        )
        self.assertIn("ids duplicados: linha01", validate(data))

    def test_invalid_attempt_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "id de segmento inválido"):
            self.parse_text("# Exemplo\n## Capítulo\n- `linha01@0` Frase.\n")


if __name__ == "__main__":
    unittest.main()
