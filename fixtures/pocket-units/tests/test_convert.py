import unittest

from pocket_units import convert


class ConvertTests(unittest.TestCase):
    def test_km_to_mile(self):
        self.assertAlmostEqual(convert.length(1.609344, "km", "mile"), 1.0)

    def test_lb_to_kg(self):
        self.assertAlmostEqual(convert.mass(1, "lb", "kg"), 0.45359237)

    def test_fahrenheit_round_trip(self):
        self.assertAlmostEqual(convert.to_celsius(convert.to_fahrenheit(21.5)), 21.5)


if __name__ == "__main__":
    unittest.main()
