"""Unit tests for concept_mapper.py."""

import unittest

from tests.unit._utils import load_module

CONCEPT_MAPPER = load_module(
    "concept_mapper",
    "skills/ontology/ontology-mapper/scripts/concept_mapper.py",
)

SAMPLE_SUMMARY = {
    "classes": {
        "Material": {
            "iri": "http://example.org/Material",
            "parent": None,
            "children": [],
            "description": "A material substance",
        },
        "Crystalline Material": {
            "iri": "http://example.org/CrystallineMaterial",
            "parent": "Material",
            "children": [],
            "description": "Periodic atomic arrangement",
        },
        "Unit Cell": {
            "iri": "http://example.org/UnitCell",
            "parent": None,
            "children": [],
            "description": None,
        },
        "Space Group": {
            "iri": "http://example.org/SpaceGroup",
            "parent": None,
            "children": [],
            "description": None,
        },
        "Lattice Parameter": {
            "iri": "http://example.org/LatticeParameter",
            "parent": None,
            "children": [],
            "description": None,
        },
    },
    "object_properties": {},
    "data_properties": {
        "has Bravais lattice": {
            "iri": "http://example.org/hasBravaisLattice",
            "domain": "Unit Cell",
            "range_type": "string",
            "description": None,
        },
    },
}

# Per-ontology synonyms (normally loaded from cmso_mappings.json)
TEST_SYNONYMS = {
    "lattice constant": "Lattice Parameter",
    "material": "Material",
    "fcc": "Crystalline Material",
    "bcc": "Crystalline Material",
    "space group": "Space Group",
    "unit cell": "Unit Cell",
}

TEST_PROPERTY_SYNONYMS = {
    "space group number": "has space group number",
}


class TestConceptMapper(unittest.TestCase):
    def test_synonym_match(self):
        result = CONCEPT_MAPPER.map_concept(
            SAMPLE_SUMMARY, term="lattice constant",
            synonyms=TEST_SYNONYMS,
        )
        self.assertTrue(len(result["matches"]) > 0)
        self.assertIn("synonym", result["matches"][0]["match_type"])
        self.assertEqual(result["matches"][0]["matched"], "Lattice Parameter")

    def test_exact_match(self):
        # Without synonyms, "Material" should get an exact match
        result = CONCEPT_MAPPER.map_concept(SAMPLE_SUMMARY, term="Material")
        self.assertTrue(len(result["matches"]) > 0)
        self.assertEqual(result["matches"][0]["matched"], "Material")
        self.assertEqual(result["matches"][0]["confidence"], 1.0)

    def test_synonym_takes_precedence_over_exact(self):
        # With synonyms, synonym match (0.9) runs before exact match (1.0)
        result = CONCEPT_MAPPER.map_concept(
            SAMPLE_SUMMARY, term="Material",
            synonyms=TEST_SYNONYMS,
        )
        self.assertTrue(len(result["matches"]) > 0)
        self.assertIn("Material", result["matches"][0]["matched"])

    def test_substring_match(self):
        result = CONCEPT_MAPPER.map_concept(SAMPLE_SUMMARY, term="crystal")
        labels = [m["matched"] for m in result["matches"]]
        self.assertIn("Crystalline Material", labels)

    def test_multiple_terms(self):
        result = CONCEPT_MAPPER.map_concept(
            SAMPLE_SUMMARY, terms=["FCC", "space group"],
            synonyms=TEST_SYNONYMS,
        )
        self.assertTrue(len(result["matches"]) >= 2)

    def test_unmatched_term(self):
        result = CONCEPT_MAPPER.map_concept(SAMPLE_SUMMARY, term="zzzznonexistent")
        self.assertIn("zzzznonexistent", result["unmatched"])

    def test_no_input_raises(self):
        with self.assertRaises(ValueError):
            CONCEPT_MAPPER.map_concept(SAMPLE_SUMMARY)

    def test_property_synonym(self):
        result = CONCEPT_MAPPER.map_concept(
            SAMPLE_SUMMARY, term="space group number",
            property_synonyms=TEST_PROPERTY_SYNONYMS,
        )
        self.assertTrue(len(result["matches"]) > 0)

    def test_no_synonyms_falls_to_generic(self):
        """Without synonyms, only generic matching (exact/substring/description) works."""
        result = CONCEPT_MAPPER.map_concept(SAMPLE_SUMMARY, term="lattice constant")
        # "lattice constant" won't match any label exactly or as substring
        # without synonyms, so it should be unmatched
        self.assertIn("lattice constant", result["unmatched"])

    def test_suggestion_is_self_contained(self):
        """F4: unmatched suggestion is a runnable, fully-pathed command with --ontology."""
        result = CONCEPT_MAPPER.map_concept(
            SAMPLE_SUMMARY, term="zzzznonexistent", ontology="cmso",
        )
        self.assertEqual(len(result["suggestions"]), 1)
        s = result["suggestions"][0]
        self.assertIn(
            "skills/ontology/ontology-explorer/scripts/class_browser.py", s
        )
        self.assertIn("--ontology cmso", s)
        self.assertIn("--search 'zzzznonexistent'", s)

    def test_suggestion_placeholder_without_ontology(self):
        """When no ontology is given, the suggestion uses a <name> placeholder."""
        result = CONCEPT_MAPPER.map_concept(SAMPLE_SUMMARY, term="zzzznonexistent")
        self.assertIn("--ontology <name>", result["suggestions"][0])

    def test_term_length_cap(self):
        """Overly long terms are rejected (security input cap)."""
        with self.assertRaises(ValueError):
            CONCEPT_MAPPER.map_concept(SAMPLE_SUMMARY, term="x" * 201)

    def test_too_many_terms(self):
        """Too many terms are rejected (security input cap)."""
        with self.assertRaises(ValueError):
            CONCEPT_MAPPER.map_concept(
                SAMPLE_SUMMARY, terms=["a"] * 101, synonyms=TEST_SYNONYMS,
            )

    def test_synonym_reported_below_exact_for_coincident_label(self):
        """F3: a term that is both a synonym key and an exact class label is 0.9, not 1.0."""
        # "space group" is both a synonym key and the exact label "Space Group".
        result = CONCEPT_MAPPER.map_concept(
            SAMPLE_SUMMARY, term="space group", synonyms=TEST_SYNONYMS,
        )
        m = result["matches"][0]
        self.assertEqual(m["matched"], "Space Group")
        self.assertEqual(m["confidence"], 0.9)
        self.assertEqual(m["match_type"], "synonym_class")


if __name__ == "__main__":
    unittest.main()
