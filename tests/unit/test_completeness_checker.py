"""Unit tests for completeness_checker.py."""

import unittest

from tests.unit._utils import load_module

COMPLETENESS = load_module(
    "completeness_checker",
    "skills/ontology/ontology-validator/scripts/completeness_checker.py",
)

SAMPLE_SUMMARY = {
    "classes": {
        "Crystal Structure": {
            "iri": "http://example.org/CrystalStructure",
            "parent": None,
            "children": [],
            "description": None,
        },
    },
    "object_properties": {
        "has unit cell": {
            "iri": "http://example.org/hasUnitCell",
            "domain": "Crystal Structure",
            "range": "Unit Cell",
            "description": None,
        },
        "has space group": {
            "iri": "http://example.org/hasSpaceGroup",
            "domain": "Crystal Structure",
            "range": "Space Group",
            "description": None,
        },
    },
    "data_properties": {},
}

CONSTRAINTS = {
    "Crystal Structure": {
        "required": ["has unit cell", "has space group"],
        "recommended": [],
        "optional": [],
    },
}


class TestCompletenessChecker(unittest.TestCase):
    def test_full_completeness(self):
        result = COMPLETENESS.check_completeness(
            SAMPLE_SUMMARY,
            CONSTRAINTS,
            "Crystal Structure",
            ["has unit cell", "has space group"],
        )
        self.assertEqual(result["completeness_score"], 1.0)
        self.assertEqual(result["required_missing"], [])

    def test_partial_completeness(self):
        result = COMPLETENESS.check_completeness(
            SAMPLE_SUMMARY,
            CONSTRAINTS,
            "Crystal Structure",
            ["has unit cell"],
        )
        self.assertEqual(result["completeness_score"], 0.5)
        self.assertIn("has space group", result["required_missing"])

    def test_empty_provided(self):
        result = COMPLETENESS.check_completeness(
            SAMPLE_SUMMARY,
            CONSTRAINTS,
            "Crystal Structure",
            [],
        )
        self.assertEqual(result["completeness_score"], 0.0)
        self.assertEqual(len(result["required_missing"]), 2)

    def test_unrecognized_property(self):
        result = COMPLETENESS.check_completeness(
            SAMPLE_SUMMARY,
            CONSTRAINTS,
            "Crystal Structure",
            ["has unit cell", "fake property"],
        )
        self.assertIn("fake property", result["unrecognized"])

    def test_case_insensitive_class(self):
        result = COMPLETENESS.check_completeness(
            SAMPLE_SUMMARY,
            CONSTRAINTS,
            "crystal structure",
            ["has unit cell"],
        )
        self.assertEqual(result["class_name"], "Crystal Structure")

    def test_class_not_found(self):
        with self.assertRaises(ValueError):
            COMPLETENESS.check_completeness(
                SAMPLE_SUMMARY, CONSTRAINTS, "Nonexistent", [],
            )

    def test_empty_class_name(self):
        with self.assertRaises(ValueError):
            COMPLETENESS.check_completeness(
                SAMPLE_SUMMARY, CONSTRAINTS, "", [],
            )

    def test_no_constraints_uses_domain_properties(self):
        result = COMPLETENESS.check_completeness(
            SAMPLE_SUMMARY,
            {},  # No constraints
            "Crystal Structure",
            ["has unit cell"],
        )
        # Without constraints, domain properties become recommended
        self.assertIn("has space group", result["recommended_missing"])


if __name__ == "__main__":
    unittest.main()
