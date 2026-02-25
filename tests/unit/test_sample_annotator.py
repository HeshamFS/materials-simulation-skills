"""Unit tests for sample_annotator.py."""

import json
import os
import unittest

from tests.unit._utils import load_module

SAMPLE_ANNOTATOR = load_module(
    "sample_annotator",
    "skills/ontology/ontology-mapper/scripts/sample_annotator.py",
)


def _load_cmso_summary():
    """Load the actual CMSO summary for realistic testing."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "skills", "ontology", "ontology-explorer", "references",
        "cmso_summary.json",
    )
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _load_cmso_mappings():
    """Load the actual CMSO mappings config for realistic testing."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "skills", "ontology", "ontology-mapper", "references",
        "cmso_mappings.json",
    )
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


class TestSampleAnnotator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = _load_cmso_summary()
        cls.mappings = _load_cmso_mappings()

    def test_fcc_copper(self):
        if not self.summary:
            self.skipTest("CMSO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "copper", "structure": "FCC", "space_group": 225,
             "lattice_a": 3.615},
            mappings=self.mappings,
        )
        self.assertEqual(result["material_type"], "Crystalline Material")
        self.assertEqual(result["sample_type"], "Atomic Scale Sample")
        # Should find Cu element
        elements = [
            a for a in result["annotations"]
            if a.get("class") == "Chemical Element"
        ]
        self.assertTrue(len(elements) > 0)
        self.assertEqual(elements[0]["value"], "Cu")

    def test_amorphous_material(self):
        if not self.summary:
            self.skipTest("CMSO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "amorphous SiO2", "elements": ["Si", "O"]},
            mappings=self.mappings,
        )
        self.assertEqual(result["material_type"], "Amorphous Material")

    def test_polycrystal(self):
        if not self.summary:
            self.skipTest("CMSO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "polycrystalline steel", "elements": ["Fe", "C"]},
            mappings=self.mappings,
        )
        self.assertEqual(result["material_type"], "Polycrystal")

    def test_unmapped_fields_reported(self):
        if not self.summary:
            self.skipTest("CMSO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "copper", "custom_field": 42},
        )
        self.assertIn("custom_field", result["unmapped_fields"])

    def test_suggested_properties(self):
        if not self.summary:
            self.skipTest("CMSO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "iron"},
        )
        # Should suggest space_group and elements
        suggestions = " ".join(result["suggested_properties"])
        self.assertIn("space_group", suggestions)

    def test_empty_sample_raises(self):
        with self.assertRaises(ValueError):
            SAMPLE_ANNOTATOR.annotate_sample({}, {})

    def test_non_dict_sample_raises(self):
        with self.assertRaises(ValueError):
            SAMPLE_ANNOTATOR.annotate_sample({}, "not a dict")

    def test_element_by_name(self):
        if not self.summary:
            self.skipTest("CMSO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "gold"},
        )
        elements = [
            a for a in result["annotations"]
            if a.get("class") == "Chemical Element"
        ]
        self.assertTrue(len(elements) > 0)
        self.assertEqual(elements[0]["value"], "Au")

    def test_generic_defaults_without_mappings(self):
        """Without mappings config, uses generic default labels."""
        if not self.summary:
            self.skipTest("CMSO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "copper", "structure": "FCC"},
            mappings=None,
        )
        # Should still classify as Crystalline Material (default rule)
        self.assertEqual(result["material_type"], "Crystalline Material")
        # Should use default sample class labels
        sample_ann = result["annotations"][0]
        self.assertEqual(sample_ann["class"], "Sample")

    def test_cmso_mappings_produce_cmso_labels(self):
        """With CMSO mappings, uses CMSO-specific class names."""
        if not self.summary or not self.mappings:
            self.skipTest("CMSO summary or mappings not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "copper", "structure": "FCC"},
            mappings=self.mappings,
        )
        sample_ann = result["annotations"][0]
        self.assertEqual(sample_ann["class"], "Computational Sample")
        self.assertEqual(sample_ann["subclass"], "Atomic Scale Sample")


if __name__ == "__main__":
    unittest.main()
