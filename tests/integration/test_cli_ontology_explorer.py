"""Integration tests for ontology-explorer CLI scripts."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.integration._schema import assert_schema

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "ontology" / "ontology-explorer" / "scripts"
SUMMARY = ROOT / "skills" / "ontology" / "ontology-explorer" / "references" / "cmso_summary.json"


class TestCliClassBrowser(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_list_roots_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "class_browser.py"),
            "--ontology", "cmso",
            "--list-roots",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        assert_schema(data, {
            "inputs": dict,
            "results": {"roots": list},
        })
        self.assertTrue(len(data["results"]["roots"]) > 0)

    def test_class_lookup_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "class_browser.py"),
            "--ontology", "cmso",
            "--class", "Material",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("class_info", data["results"])
        self.assertIn("subtree", data["results"])
        self.assertIn("path_to_root", data["results"])

    def test_search_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "class_browser.py"),
            "--ontology", "cmso",
            "--search", "crystal",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("search_results", data["results"])

    def test_invalid_ontology_exit_code(self):
        result = self.run_cmd([
            str(SCRIPTS / "class_browser.py"),
            "--ontology", "nonexistent",
            "--list-roots",
            "--json",
        ])
        self.assertEqual(result.returncode, 2)


class TestCliPropertyLookup(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_property_lookup_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "property_lookup.py"),
            "--ontology", "cmso",
            "--property", "has material",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("property_info", data["results"])

    def test_class_properties_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "property_lookup.py"),
            "--ontology", "cmso",
            "--class", "Unit Cell",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("class_properties", data["results"])

    def test_search_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "property_lookup.py"),
            "--ontology", "cmso",
            "--search", "length",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("search_results", data["results"])


if __name__ == "__main__":
    unittest.main()
