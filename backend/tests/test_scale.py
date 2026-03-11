import pytest
from ..scale import Scale

def test_parse_weight_line_valid():
    tests = [
        ("   123.45 g", 123.45, "g"),
        (" +   12.34 kg \r\n", 12.34, "kg"),
        ("  - 9.01 oz ", -9.01, "oz"),
        ("0.0g", 0.0, "g"),
        ("5000g", 5000.0, "g"),
    ]

    for line, expected_wt, expected_unit in tests:
        wt, unit = Scale.parse_weight_line(line)
        assert wt == expected_wt, f"Failed on {line}: got weight {wt}"
        assert unit == expected_unit, f"Failed on {line}: got unit {unit}"

def test_parse_weight_line_invalid():
    tests = [
        "",
        "garbage string",
        "  +  - g ",
        " 123 ",
    ]

    for line in tests:
        wt, unit = Scale.parse_weight_line(line)
        assert wt is None, f"Expected None weight for {line}"
        assert unit is None, f"Expected None unit for {line}"
