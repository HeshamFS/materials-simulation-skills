"""Unit tests for property_lookup.py."""

import unittest

from tests.unit._utils import load_module

PROP_LOOKUP = load_module(
    "property_lookup",
    "skills/ontology/ontology-explorer/scripts/property_lookup.py",
)

SAMPLE_SUMMARY = {
    "classes": {},
    "object_properties": {
        "has material": {
            "iri": "http://example.org/hasMaterial",
            "domain": "Computational Sample",
            "range": "Material",
            "description": "Links sample to material",
        },
        "has structure": {
            "iri": "http://example.org/hasStructure",
            "domain": "Material",
            "range": "Structure",
            "description": None,
        },
    },
    "data_properties": {
        "has length x": {
            "iri": "http://example.org/hasLength_x",
            "domain": "Unit Cell",
            "range_type": "float",
            "description": "X component of lattice parameter",
        },
        "has name": {
            "iri": "http://example.org/hasName",
            "domain": "Thing",
            "range_type": "string",
            "description": None,
        },
    },
}


class TestPropertyLookup(unittest.TestCase):
    def test_lookup_by_name(self):
        result = PROP_LOOKUP.lookup_property(
            SAMPLE_SUMMARY, property_name="has material",
        )
        self.assertEqual(result["property_info"]["name"], "has material")
        self.assertEqual(result["property_info"]["type"], "object")
        self.assertEqual(result["property_info"]["domain"], "Computational Sample")

    def test_lookup_case_insensitive(self):
        result = PROP_LOOKUP.lookup_property(
            SAMPLE_SUMMARY, property_name="Has Material",
        )
        self.assertEqual(result["property_info"]["name"], "has material")

    def test_lookup_partial_match(self):
        result = PROP_LOOKUP.lookup_property(
            SAMPLE_SUMMARY, property_name="length",
        )
        self.assertEqual(result["property_info"]["name"], "has length x")

    def test_lookup_data_property(self):
        result = PROP_LOOKUP.lookup_property(
            SAMPLE_SUMMARY, property_name="has length x",
        )
        self.assertEqual(result["property_info"]["type"], "data")
        self.assertEqual(result["property_info"]["range_type"], "float")

    def test_class_properties(self):
        result = PROP_LOOKUP.lookup_property(
            SAMPLE_SUMMARY, class_name="Material",
        )
        names = [p["name"] for p in result["class_properties"]]
        self.assertIn("has structure", names)

    def test_class_properties_filter_type(self):
        result = PROP_LOOKUP.lookup_property(
            SAMPLE_SUMMARY, class_name="Unit Cell", prop_type="data",
        )
        names = [p["name"] for p in result["class_properties"]]
        self.assertIn("has length x", names)

    def test_search(self):
        result = PROP_LOOKUP.lookup_property(
            SAMPLE_SUMMARY, search="length",
        )
        names = [p["name"] for p in result["search_results"]]
        self.assertIn("has length x", names)

    def test_property_not_found(self):
        with self.assertRaises(ValueError):
            PROP_LOOKUP.lookup_property(
                SAMPLE_SUMMARY, property_name="nonexistent",
            )

    def test_no_query_mode_raises(self):
        with self.assertRaises(ValueError):
            PROP_LOOKUP.lookup_property(SAMPLE_SUMMARY)


if __name__ == "__main__":
    unittest.main()
