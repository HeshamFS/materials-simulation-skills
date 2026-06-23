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


def _load_asmo_summary():
    """Load the actual ASMO summary for realistic testing."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "skills", "ontology", "ontology-explorer", "references",
        "asmo_summary.json",
    )
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def _load_asmo_mappings():
    """Load the actual ASMO mappings config for realistic testing."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..",
        "skills", "ontology", "ontology-mapper", "references",
        "asmo_mappings.json",
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

    def test_cmso_sample_has_no_validation_warnings(self):
        """CMSO crystal/sample terms all resolve, so no validation warnings."""
        if not self.summary or not self.mappings:
            self.skipTest("CMSO summary or mappings not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "copper", "structure": "FCC", "space_group": 225,
             "lattice_a": 3.615},
            mappings=self.mappings,
        )
        self.assertEqual(result["validation_warnings"], [])
        for ann in result["annotations"]:
            self.assertNotIn("validation_warning", ann)


class TestSampleAnnotatorAsmoRegression(unittest.TestCase):
    """F1 regression: ASMO has no crystal/sample vocabulary, so crystalline
    sample terms must be flagged, not silently emitted as valid annotations."""

    @classmethod
    def setUpClass(cls):
        cls.summary = _load_asmo_summary()
        cls.mappings = _load_asmo_mappings()

    def test_asmo_mappings_have_no_crystal_config(self):
        """asmo_mappings.json must not ship crystal/sample blocks."""
        if not self.mappings:
            self.skipTest("ASMO mappings not available")
        for forbidden in (
            "crystal_output", "sample_schema",
            "material_type_rules", "annotation_routing",
        ):
            self.assertNotIn(
                forbidden, self.mappings,
                f"asmo_mappings.json should not define '{forbidden}'",
            )
        # Concept-mapping path remains supported.
        self.assertIn("synonyms", self.mappings)

    def test_asmo_crystal_sample_terms_flagged(self):
        """Crystalline sample for ASMO -> validation warnings, confidence 0.0."""
        if not self.summary:
            self.skipTest("ASMO summary not available")
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self.summary,
            {"material": "copper", "structure": "FCC", "lattice_a": 3.615,
             "space_group": 225},
            mappings=self.mappings,
        )
        # Crystal/sample terms are not in ASMO -> warnings present.
        self.assertTrue(len(result["validation_warnings"]) > 0)
        # Every flagged annotation has confidence 0.0 and a warning field.
        flagged = [
            a for a in result["annotations"] if "validation_warning" in a
        ]
        self.assertTrue(len(flagged) > 0)
        for ann in flagged:
            self.assertEqual(ann["confidence"], 0.0)
        # The crystal-structure terms specifically are flagged.
        joined = " ".join(result["validation_warnings"])
        self.assertIn("Crystal Structure", joined)
        self.assertIn("Unit Cell", joined)


class TestSampleAnnotatorSecurity(unittest.TestCase):
    """Input-validation hardening claimed in SKILL.md Security section."""

    _SUMMARY = {"classes": {}, "object_properties": {}, "data_properties": {}}

    def test_too_many_keys_rejected(self):
        big = {f"k{i}": i for i in range(101)}
        with self.assertRaises(ValueError):
            SAMPLE_ANNOTATOR.annotate_sample(self._SUMMARY, big)

    def test_oversized_string_value_rejected(self):
        with self.assertRaises(ValueError):
            SAMPLE_ANNOTATOR.annotate_sample(
                self._SUMMARY, {"material": "x" * 501},
            )

    def test_validation_disabled_for_empty_summary(self):
        """An empty classes table disables validation (generic/test usage)."""
        result = SAMPLE_ANNOTATOR.annotate_sample(
            self._SUMMARY, {"material": "copper", "structure": "FCC"},
        )
        self.assertEqual(result["validation_warnings"], [])


if __name__ == "__main__":
    unittest.main()
