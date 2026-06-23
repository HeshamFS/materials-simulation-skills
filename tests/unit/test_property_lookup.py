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


# Summary with a populated class index, used to test canonical resolution of
# spaceless class names (regression for the UnitCell empty-result bug).
SUMMARY_WITH_CLASSES = {
    "classes": {
        "Unit Cell": {"parent": "Structure", "children": []},
        "Structure": {"parent": None, "children": ["Unit Cell"]},
        "Material": {"parent": None, "children": []},
    },
    "object_properties": {
        "has unit cell": {
            "iri": "http://example.org/hasUnitCell",
            "domain": "Crystal Structure",
            "range": "Unit Cell",
            "description": None,
        },
    },
    "data_properties": {
        "has lattice parameter": {
            "iri": "http://example.org/hasLatticeParameter",
            "domain": "Unit Cell",
            "range_type": "float",
            "description": None,
        },
        "has basis": {
            "iri": "http://example.org/hasBasis",
            "domain": "UnitCell",  # union-style / spaceless canonical token
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

    # --- Regression: spaceless class name resolves to canonical label (F1) ---
    def test_class_properties_spaceless_name_matches(self):
        result = PROP_LOOKUP.lookup_property(
            SUMMARY_WITH_CLASSES, class_name="UnitCell",
        )
        names = [p["name"] for p in result["class_properties"]]
        # Both the "Unit Cell"-domain prop and the spaceless-domain prop match.
        self.assertIn("has lattice parameter", names)
        self.assertIn("has basis", names)
        # class_name is reported as the canonical label, not the raw input.
        self.assertEqual(result["class_name"], "Unit Cell")

    def test_class_properties_spaced_and_spaceless_agree(self):
        spaced = PROP_LOOKUP.lookup_property(
            SUMMARY_WITH_CLASSES, class_name="Unit Cell",
        )
        spaceless = PROP_LOOKUP.lookup_property(
            SUMMARY_WITH_CLASSES, class_name="UnitCell",
        )
        self.assertEqual(
            [p["name"] for p in spaced["class_properties"]],
            [p["name"] for p in spaceless["class_properties"]],
        )

    def test_unknown_class_raises_when_index_present(self):
        with self.assertRaises(ValueError):
            PROP_LOOKUP.lookup_property(
                SUMMARY_WITH_CLASSES, class_name="Nonexistent",
            )

    # --- Security hardening ---
    def test_unsafe_class_name_rejected(self):
        with self.assertRaises(ValueError):
            PROP_LOOKUP.lookup_property(SAMPLE_SUMMARY, class_name="foo;rm")

    def test_overlong_search_rejected(self):
        with self.assertRaises(ValueError):
            PROP_LOOKUP.lookup_property(SAMPLE_SUMMARY, search="a" * 200)

    def test_search_results_capped(self):
        many = {
            "classes": {},
            "object_properties": {
                f"prop x{i}": {
                    "iri": f"http://example.org/p{i}",
                    "domain": "X",
                    "range": "Y",
                    "description": None,
                }
                for i in range(300)
            },
            "data_properties": {},
        }
        result = PROP_LOOKUP.lookup_property(many, search="prop x")
        self.assertLessEqual(
            len(result["search_results"]), PROP_LOOKUP._MAX_RESULTS,
        )


if __name__ == "__main__":
    unittest.main()
