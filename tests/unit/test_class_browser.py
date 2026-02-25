"""Unit tests for class_browser.py."""

import unittest

from tests.unit._utils import load_module

CLASS_BROWSER = load_module(
    "class_browser",
    "skills/ontology/ontology-explorer/scripts/class_browser.py",
)

SAMPLE_SUMMARY = {
    "classes": {
        "Material": {
            "iri": "http://example.org/Material",
            "parent": None,
            "children": ["Crystalline Material", "Amorphous Material"],
            "description": "A material substance",
        },
        "Crystalline Material": {
            "iri": "http://example.org/CrystallineMaterial",
            "parent": "Material",
            "children": ["Bicrystal"],
            "description": "Periodic atomic arrangement",
        },
        "Amorphous Material": {
            "iri": "http://example.org/AmorphousMaterial",
            "parent": "Material",
            "children": [],
            "description": "No long-range order",
        },
        "Bicrystal": {
            "iri": "http://example.org/Bicrystal",
            "parent": "Crystalline Material",
            "children": [],
            "description": None,
        },
    },
    "object_properties": {
        "has structure": {
            "iri": "http://example.org/hasStructure",
            "domain": "Material",
            "range": "Structure",
            "description": None,
        },
    },
    "data_properties": {
        "has name": {
            "iri": "http://example.org/hasName",
            "domain": "Material",
            "range_type": "string",
            "description": None,
        },
    },
}


class TestClassBrowser(unittest.TestCase):
    def test_list_roots(self):
        result = CLASS_BROWSER.browse_class(SAMPLE_SUMMARY, list_roots=True)
        self.assertIn("Material", result["roots"])

    def test_class_info(self):
        result = CLASS_BROWSER.browse_class(
            SAMPLE_SUMMARY, class_name="Material",
        )
        self.assertEqual(result["class_info"]["label"], "Material")
        self.assertIn("Crystalline Material", result["class_info"]["children"])

    def test_path_to_root(self):
        result = CLASS_BROWSER.browse_class(
            SAMPLE_SUMMARY, class_name="Bicrystal",
        )
        self.assertEqual(
            result["path_to_root"],
            ["Material", "Crystalline Material", "Bicrystal"],
        )

    def test_subtree(self):
        result = CLASS_BROWSER.browse_class(
            SAMPLE_SUMMARY, class_name="Material",
        )
        self.assertIn("Crystalline Material", result["subtree"])
        self.assertIn("Bicrystal", result["subtree"]["Crystalline Material"])

    def test_subtree_depth_limit(self):
        result = CLASS_BROWSER.browse_class(
            SAMPLE_SUMMARY, class_name="Material", depth=1,
        )
        # Depth 1 shows children but not grandchildren
        self.assertIn("Crystalline Material", result["subtree"])
        self.assertEqual(result["subtree"]["Crystalline Material"], {})

    def test_search(self):
        result = CLASS_BROWSER.browse_class(
            SAMPLE_SUMMARY, search="crystal",
        )
        labels = [m["label"] for m in result["search_results"]]
        self.assertIn("Crystalline Material", labels)
        self.assertIn("Bicrystal", labels)

    def test_case_insensitive_lookup(self):
        result = CLASS_BROWSER.browse_class(
            SAMPLE_SUMMARY, class_name="material",
        )
        self.assertEqual(result["class_info"]["label"], "Material")

    def test_applicable_properties(self):
        result = CLASS_BROWSER.browse_class(
            SAMPLE_SUMMARY, class_name="Material",
        )
        obj_names = [p["name"] for p in result["properties"]["object_properties"]]
        self.assertIn("has structure", obj_names)
        data_names = [p["name"] for p in result["properties"]["data_properties"]]
        self.assertIn("has name", data_names)

    def test_class_not_found(self):
        with self.assertRaises(ValueError):
            CLASS_BROWSER.browse_class(
                SAMPLE_SUMMARY, class_name="Nonexistent",
            )

    def test_no_query_mode_raises(self):
        with self.assertRaises(ValueError):
            CLASS_BROWSER.browse_class(SAMPLE_SUMMARY)


if __name__ == "__main__":
    unittest.main()
