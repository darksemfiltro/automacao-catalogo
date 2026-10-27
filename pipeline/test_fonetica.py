"""Speech normalization regressions for common measurements."""

import unittest

from fonetica import PEND, normaliza


class FoneticaTests(unittest.TestCase):
    def test_thousand_separators_stay_attached_to_units(self):
        cases = {
            "1.000 km²": "mil quilômetros quadrados",
            "2.500 km": "dois mil e quinhentos quilômetros",
            "3.000 kg": "três mil quilogramas",
        }
        for original, expected in cases.items():
            with self.subTest(original=original):
                spoken = normaliza(original)
                self.assertEqual(expected, spoken)
                self.assertIsNone(PEND.search(spoken))

    def test_feminine_ton_and_negative_celsius(self):
        self.assertEqual("duas toneladas", normaliza("2 toneladas"))
        self.assertEqual("vinte e duas toneladas", normaliza("22 toneladas"))
        self.assertEqual("menos três graus", normaliza("-3°C"))
        self.assertEqual("três graus", normaliza("3°C"))

    def test_existing_decimal_ton_output_is_preserved(self):
        self.assertEqual("cinco vírgula cinco toneladas", normaliza("5,5 toneladas"))


if __name__ == "__main__":
    unittest.main()
