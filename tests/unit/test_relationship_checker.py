"""Unit tests for relationship_checker.py."""

import unittest

from tests.unit._utils import load_module

REL_CHECKER = load_module(
    "relationship_checker",
    "skills/ontology/ontology-validator/scripts/relationship_checker.py",
)

SAMPLE_SUMMARY = {
    "classes": {
        "Computational Sample": {
            "iri": "http://example.org/ComputationalSample",
            "parent": None,
            "children": ["Atomic Scale Sample"],
            "description": None,
        },
        "Atomic Scale Sample": {
            "iri": "http://example.org/AtomicScaleSample",
            "parent": "Computational Sample",
            "children": [],
            "description": None,
        },
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
    "data_properties": {},
}


class TestRelationshipChecker(unittest.TestCase):
    def test_valid_relationship(self):
        result = REL_CHECKER.check_relationships(
            SAMPLE_SUMMARY,
            [{"subject_class": "Computational Sample",
              "property": "has material",
              "object_class": "Material"}],
        )
        self.assertTrue(result["valid"])
        self.assertTrue(result["results"][0]["valid"])

    def test_subclass_subject_valid(self):
        """Atomic Scale Sample is subclass of Computational Sample."""
        result = REL_CHECKER.check_relationships(
            SAMPLE_SUMMARY,
            [{"subject_class": "Atomic Scale Sample",
              "property": "has material",
              "object_class": "Material"}],
        )
        self.assertTrue(result["valid"])

    def test_subclass_object_valid(self):
        """Crystalline Material is subclass of Material."""
        result = REL_CHECKER.check_relationships(
            SAMPLE_SUMMARY,
            [{"subject_class": "Computational Sample",
              "property": "has material",
              "object_class": "Crystalline Material"}],
        )
        self.assertTrue(result["valid"])

    def test_invalid_domain(self):
        result = REL_CHECKER.check_relationships(
            SAMPLE_SUMMARY,
            [{"subject_class": "Unit Cell",
              "property": "has material",
              "object_class": "Material"}],
        )
        self.assertFalse(result["valid"])
        self.assertFalse(result["results"][0]["valid"])

    def test_invalid_range(self):
        result = REL_CHECKER.check_relationships(
            SAMPLE_SUMMARY,
            [{"subject_class": "Computational Sample",
              "property": "has material",
              "object_class": "Unit Cell"}],
        )
        self.assertFalse(result["valid"])

    def test_unknown_property(self):
        result = REL_CHECKER.check_relationships(
            SAMPLE_SUMMARY,
            [{"subject_class": "Computational Sample",
              "property": "fake property",
              "object_class": "Material"}],
        )
        self.assertFalse(result["valid"])

    def test_multiple_relationships(self):
        result = REL_CHECKER.check_relationships(
            SAMPLE_SUMMARY,
            [
                {"subject_class": "Computational Sample",
                 "property": "has material",
                 "object_class": "Material"},
                {"subject_class": "Unit Cell",
                 "property": "has material",
                 "object_class": "Material"},
            ],
        )
        self.assertFalse(result["valid"])
        self.assertTrue(result["results"][0]["valid"])
        self.assertFalse(result["results"][1]["valid"])

    def test_empty_list_raises(self):
        with self.assertRaises(ValueError):
            REL_CHECKER.check_relationships(SAMPLE_SUMMARY, [])

    def test_non_list_raises(self):
        with self.assertRaises(ValueError):
            REL_CHECKER.check_relationships(SAMPLE_SUMMARY, "not a list")


if __name__ == "__main__":
    unittest.main()
