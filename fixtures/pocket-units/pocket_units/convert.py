"""Conversion functions built on the factor tables."""

from pocket_units.core.tables import LENGTH_METRES, MASS_KG


def length(value, from_unit, to_unit):
    """Convert a length between any two units in LENGTH_METRES."""
    metres = value * LENGTH_METRES[from_unit]
    return metres / LENGTH_METRES[to_unit]


def mass(value, from_unit, to_unit):
    """Convert a mass between any two units in MASS_KG."""
    kg = value * MASS_KG[from_unit]
    return kg / MASS_KG[to_unit]


def to_fahrenheit(celsius):
    """Convert degrees Celsius to degrees Fahrenheit."""
    return celsius * 9 / 5 + 32


def to_celsius(fahrenheit):
    """Convert degrees Fahrenheit to degrees Celsius."""
    return (fahrenheit - 32) * 5 / 9
