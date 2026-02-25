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


if __name__ == "__main__":
    unittest.main()
