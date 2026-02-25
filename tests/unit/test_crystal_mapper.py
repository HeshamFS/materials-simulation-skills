"""Unit tests for crystal_mapper.py."""

import unittest

from tests.unit._utils import load_module

CRYSTAL_MAPPER = load_module(
    "crystal_mapper",
    "skills/ontology/ontology-mapper/scripts/crystal_mapper.py",
)

# CMSO-specific output config (normally loaded from cmso_mappings.json)
CMSO_CRYSTAL_OUTPUT = {
    "base_classes": [
        "Computational Sample",
        "Atomic Scale Sample",
        "Crystalline Material",
        "Crystal Structure",
        "Unit Cell",
    ],
    "space_group_class": "Space Group",
    "lattice_parameter_class": "Lattice Parameter",
    "property_map": {
        "bravais_lattice": "has Bravais lattice",
        "space_group_number": "has space group number",
        "length_x": "has length x",
        "length_y": "has length y",
        "length_z": "has length z",
        "angle_alpha": "has angle alpha",
        "angle_beta": "has angle beta",
        "angle_gamma": "has angle gamma",
    },
}


class TestCrystalMapper(unittest.TestCase):
    def test_cubic_fcc(self):
        result = CRYSTAL_MAPPER.map_crystal(
            bravais="FCC", space_group=225, a=3.615,
            crystal_output=CMSO_CRYSTAL_OUTPUT,
        )
        self.assertEqual(result["bravais_lattice"], "cF")
        self.assertEqual(result["effective_system"], "cubic")
        self.assertIn("Unit Cell", result["ontology_classes"])
        self.assertIn("Space Group", result["ontology_classes"])

    def test_bcc(self):
        result = CRYSTAL_MAPPER.map_crystal(bravais="BCC", a=2.87)
        self.assertEqual(result["bravais_lattice"], "cI")

    def test_hexagonal(self):
        result = CRYSTAL_MAPPER.map_crystal(
            system="hexagonal", a=3.21, c=5.21,
        )
        self.assertEqual(result["effective_system"], "hexagonal")

    def test_space_group_infers_system(self):
        result = CRYSTAL_MAPPER.map_crystal(space_group=225)
        self.assertEqual(result["inferred_system"], "cubic")

    def test_system_space_group_mismatch_warning(self):
        result = CRYSTAL_MAPPER.map_crystal(
            system="hexagonal", space_group=225,
        )
        self.assertTrue(len(result["validation_warnings"]) > 0)

    def test_cubic_lattice_mismatch_warning(self):
        result = CRYSTAL_MAPPER.map_crystal(
            system="cubic", a=3.0, b=4.0,
        )
        warnings = result["validation_warnings"]
        self.assertTrue(any("a=b" in w for w in warnings))

    def test_properties_include_lattice(self):
        result = CRYSTAL_MAPPER.map_crystal(
            a=3.615, alpha=90.0,
            crystal_output=CMSO_CRYSTAL_OUTPUT,
        )
        props = {p["property"] for p in result["ontology_properties"]}
        self.assertIn("has length x", props)
        self.assertIn("has angle alpha", props)

    def test_invalid_space_group(self):
        with self.assertRaises(ValueError):
            CRYSTAL_MAPPER.map_crystal(space_group=0)
        with self.assertRaises(ValueError):
            CRYSTAL_MAPPER.map_crystal(space_group=231)

    def test_negative_lattice_param(self):
        with self.assertRaises(ValueError):
            CRYSTAL_MAPPER.map_crystal(a=-1.0)

    def test_nan_rejection(self):
        with self.assertRaises(ValueError):
            CRYSTAL_MAPPER.map_crystal(a=float("nan"))

    def test_inf_rejection(self):
        with self.assertRaises(ValueError):
            CRYSTAL_MAPPER.map_crystal(a=float("inf"))

    def test_angle_out_of_range(self):
        with self.assertRaises(ValueError):
            CRYSTAL_MAPPER.map_crystal(alpha=0.0)
        with self.assertRaises(ValueError):
            CRYSTAL_MAPPER.map_crystal(alpha=180.0)

    def test_all_space_groups(self):
        """Every valid space group (1-230) should map to a system."""
        for sg in range(1, 231):
            result = CRYSTAL_MAPPER.map_crystal(space_group=sg)
            self.assertIsNotNone(
                result["inferred_system"],
                f"Space group {sg} did not infer a system",
            )

    def test_generic_output_without_config(self):
        """Without ontology config, output uses generic labels."""
        result = CRYSTAL_MAPPER.map_crystal(
            bravais="FCC", space_group=225, a=3.615,
        )
        # Should use default generic labels
        self.assertIn("ontology_classes", result)
        self.assertIn("ontology_properties", result)
        # Generic property names
        props = {p["property"] for p in result["ontology_properties"]}
        self.assertIn("bravais_lattice", props)

    def test_ontology_specific_output_with_config(self):
        """With CMSO config, output uses CMSO-specific labels."""
        result = CRYSTAL_MAPPER.map_crystal(
            bravais="FCC", space_group=225, a=3.615,
            crystal_output=CMSO_CRYSTAL_OUTPUT,
        )
        props = {p["property"] for p in result["ontology_properties"]}
        self.assertIn("has Bravais lattice", props)
        self.assertIn("has space group number", props)
        self.assertIn("has length x", props)


if __name__ == "__main__":
    unittest.main()
