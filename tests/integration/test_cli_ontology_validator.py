"""Integration tests for ontology-validator CLI scripts."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "ontology" / "ontology-validator" / "scripts"


class TestCliSchemaChecker(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_annotation_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "schema_checker.py"),
            "--ontology", "cmso",
            "--annotation",
            '{"class":"Unit Cell","properties":{"has Bravais lattice":"cF"}}',
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["results"]["valid"])

    def test_invalid_class_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "schema_checker.py"),
            "--ontology", "cmso",
            "--annotation",
            '{"class":"FakeClass"}',
            "--json",
        ])
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertFalse(data["results"]["valid"])

    def test_bad_json_exit_code(self):
        result = self.run_cmd([
            str(SCRIPTS / "schema_checker.py"),
            "--ontology", "cmso",
            "--annotation", "not json",
            "--json",
        ])
        self.assertEqual(result.returncode, 2)


class TestCliCompletenessChecker(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_completeness_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "completeness_checker.py"),
            "--ontology", "cmso",
            "--class", "Crystal Structure",
            "--provided", "has unit cell,has space group",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("completeness_score", data["results"])

    def test_unknown_class_exit_code(self):
        result = self.run_cmd([
            str(SCRIPTS / "completeness_checker.py"),
            "--ontology", "cmso",
            "--class", "NonexistentClass",
            "--provided", "foo",
            "--json",
        ])
        self.assertEqual(result.returncode, 2)


class TestCliRelationshipChecker(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_valid_relationship_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "relationship_checker.py"),
            "--ontology", "cmso",
            "--relationships",
            '[{"subject_class":"Computational Sample","property":"has material","object_class":"Material"}]',
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(data["results"]["valid"])

    def test_invalid_domain_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "relationship_checker.py"),
            "--ontology", "cmso",
            "--relationships",
            '[{"subject_class":"Unit Cell","property":"has material","object_class":"Material"}]',
            "--json",
        ])
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertFalse(data["results"]["valid"])


if __name__ == "__main__":
    unittest.main()
