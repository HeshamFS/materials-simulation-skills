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


# Summary exercising subclass / substring relationships for F1 regression.
SUBCLASS_SUMMARY = {
    "classes": {
        "Material": {"parent": None, "children": ["Crystalline Material"]},
        "Crystalline Material": {"parent": "Material", "children": []},
        "Unit": {"parent": None, "children": []},
        "Unit Cell": {"parent": None, "children": []},
    },
    "object_properties": {
        "has structure": {"domain": "Material", "range": "Structure"},
        "has crystallographic defect": {
            "domain": "Crystalline Material", "range": "Crystal Defect",
        },
        "has Bravais lattice": {"domain": "Unit Cell", "range": "string"},
    },
    "data_properties": {},
}


class TestSubclassDomainMatching(unittest.TestCase):
    def test_bare_material_excludes_subclass_property(self):
        # F1: "Material" (substring of "Crystalline Material") must NOT be
        # credited with the subclass-only "has crystallographic defect".
        result = COMPLETENESS.check_completeness(
            SUBCLASS_SUMMARY, {}, "Material", [],
        )
        self.assertIn("has structure", result["recommended_missing"])
        self.assertNotIn(
            "has crystallographic defect", result["recommended_missing"]
        )

    def test_unit_excludes_unit_cell_property(self):
        # F1: "Unit" must NOT inherit "Unit Cell" properties via substring.
        result = COMPLETENESS.check_completeness(
            SUBCLASS_SUMMARY, {}, "Unit", [],
        )
        self.assertEqual(result["recommended_missing"], [])

    def test_subclass_inherits_parent_property(self):
        # "Crystalline Material" IS-A "Material" so it gets both properties.
        result = COMPLETENESS.check_completeness(
            SUBCLASS_SUMMARY, {}, "Crystalline Material", [],
        )
        self.assertIn("has structure", result["recommended_missing"])
        self.assertIn(
            "has crystallographic defect", result["recommended_missing"]
        )


class TestCompletenessSecurity(unittest.TestCase):
    def test_too_many_provided_raises(self):
        with self.assertRaises(ValueError):
            COMPLETENESS.check_completeness(
                SAMPLE_SUMMARY, CONSTRAINTS, "Crystal Structure",
                ["p"] * (COMPLETENESS.MAX_PROVIDED + 1),
            )

    def test_overlong_class_name_raises(self):
        with self.assertRaises(ValueError):
            COMPLETENESS.check_completeness(
                SAMPLE_SUMMARY, CONSTRAINTS,
                "X" * (COMPLETENESS.MAX_NAME_LEN + 1), [],
            )


if __name__ == "__main__":
    unittest.main()
