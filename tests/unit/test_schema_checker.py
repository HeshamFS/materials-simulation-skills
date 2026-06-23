"""Unit tests for schema_checker.py."""

import unittest

from tests.unit._utils import load_module

SCHEMA_CHECKER = load_module(
    "schema_checker",
    "skills/ontology/ontology-validator/scripts/schema_checker.py",
)

SAMPLE_SUMMARY = {
    "classes": {
        "Material": {
            "iri": "http://example.org/Material",
            "parent": None,
            "children": ["Crystalline Material"],
            "description": None,
        },
        "Crystalline Material": {
            "iri": "http://example.org/CrystallineMaterial",
            "parent": "Material",
            "children": [],
            "description": None,
        },
        "Unit": {
            "iri": "http://example.org/Unit",
            "parent": None,
            "children": [],
            "description": None,
        },
        "Unit Cell": {
            "iri": "http://example.org/UnitCell",
            "parent": None,
            "children": [],
            "description": None,
        },
    },
    "object_properties": {
        "has material": {
            "iri": "http://example.org/hasMaterial",
            "domain": "Computational Sample",
            "range": "Material",
            "description": None,
        },
        "has crystallographic defect": {
            "iri": "http://example.org/hasDefect",
            "domain": "Crystalline Material",
            "range": "Crystal Defect",
            "description": None,
        },
    },
    "data_properties": {
        "has Bravais lattice": {
            "iri": "http://example.org/hasBravaisLattice",
            "domain": "Unit Cell",
            "range_type": "string",
            "description": None,
        },
    },
}


class TestSchemaChecker(unittest.TestCase):
    def test_valid_annotation(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Unit Cell", "properties": {"has Bravais lattice": "cF"}},
        )
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)

    def test_unknown_class(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "FakeClass"},
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any(e["error_type"] == "unknown_class" for e in result["errors"])
        )

    def test_unknown_property(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Unit Cell", "properties": {"fake prop": "value"}},
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any(e["error_type"] == "unknown_property" for e in result["errors"])
        )

    def test_domain_mismatch_warning(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Material", "properties": {"has Bravais lattice": "cF"}},
        )
        # Domain mismatch should be a warning, not error
        self.assertTrue(result["valid"])
        self.assertTrue(
            any(w["warning_type"] == "domain_mismatch" for w in result["warnings"])
        )

    def test_annotation_list(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"annotations": [
                {"class": "Material"},
                {"class": "Unit Cell"},
            ]},
        )
        self.assertTrue(result["valid"])

    def test_single_property_field(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Unit Cell", "property": "has Bravais lattice", "value": "cF"},
        )
        self.assertTrue(result["valid"])
        self.assertTrue(result["properties_valid"]["has Bravais lattice"])

    def test_non_dict_raises(self):
        with self.assertRaises(ValueError):
            SCHEMA_CHECKER.check_schema(SAMPLE_SUMMARY, {}, "not a dict")

    # --- F1 regression: subclass-aware domain matching ---
    def test_domain_mismatch_false_negative_substring(self):
        # "Unit" is a substring of "Unit Cell"; a "Unit Cell"-domain property
        # applied to "Unit" must still warn (was a false negative).
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Unit", "properties": {"has Bravais lattice": "cF"}},
        )
        self.assertTrue(
            any(w["warning_type"] == "domain_mismatch" for w in result["warnings"])
        )

    def test_domain_match_subclass_no_warning(self):
        # A "Material"-domain property applied to its subclass should not warn;
        # and a "Crystalline Material" property applied to the subclass is fine.
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Crystalline Material",
             "properties": {"has crystallographic defect": True}},
        )
        self.assertEqual(result["warnings"], [])

    def test_domain_mismatch_superclass_warns(self):
        # A "Crystalline Material" property applied to the *parent* "Material"
        # must warn: Material is NOT a subclass of Crystalline Material.
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Material",
             "properties": {"has crystallographic defect": True}},
        )
        self.assertTrue(
            any(w["warning_type"] == "domain_mismatch" for w in result["warnings"])
        )

    # --- F6 regression: nearest-match suggestions ---
    def test_unknown_class_suggestions(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Unit Celll", "properties": {}},
        )
        err = next(e for e in result["errors"]
                   if e["error_type"] == "unknown_class")
        self.assertIn("Unit Cell", err["suggestions"])
        self.assertIn("did you mean", err["message"])

    def test_unknown_property_suggestions(self):
        result = SCHEMA_CHECKER.check_schema(
            SAMPLE_SUMMARY,
            {},
            {"class": "Unit Cell",
             "properties": {"has_Bravais_lattice": "cF"}},
        )
        err = next(e for e in result["errors"]
                   if e["error_type"] == "unknown_property")
        self.assertIn("has Bravais lattice", err["suggestions"])

    # --- Security: input caps ---
    def test_too_many_properties_raises(self):
        props = {f"p{i}": 1 for i in range(SCHEMA_CHECKER.MAX_PROPERTIES + 1)}
        with self.assertRaises(ValueError):
            SCHEMA_CHECKER.check_schema(
                SAMPLE_SUMMARY, {}, {"class": "Unit Cell", "properties": props}
            )

    def test_overlong_class_name_raises(self):
        with self.assertRaises(ValueError):
            SCHEMA_CHECKER.check_schema(
                SAMPLE_SUMMARY, {},
                {"class": "X" * (SCHEMA_CHECKER.MAX_NAME_LEN + 1)},
            )


if __name__ == "__main__":
    unittest.main()
