"""Integration tests for ontology-mapper CLI scripts."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "ontology" / "ontology-mapper" / "scripts"


class TestCliConceptMapper(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_single_term_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "concept_mapper.py"),
            "--ontology", "cmso",
            "--term", "unit cell",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertIn("matches", data["results"])

    def test_multiple_terms_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "concept_mapper.py"),
            "--ontology", "cmso",
            "--terms", "FCC,copper,space group",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertTrue(len(data["results"]["matches"]) >= 2)


class TestCliCrystalMapper(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_fcc_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "crystal_mapper.py"),
            "--ontology", "cmso",
            "--bravais", "FCC",
            "--space-group", "225",
            "--a", "3.615",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["results"]["bravais_lattice"], "cF")
        self.assertEqual(data["results"]["effective_system"], "cubic")

    def test_fcc_json_without_ontology(self):
        """crystal_mapper works without --ontology, using generic labels."""
        result = self.run_cmd([
            str(SCRIPTS / "crystal_mapper.py"),
            "--bravais", "FCC",
            "--space-group", "225",
            "--a", "3.615",
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["results"]["bravais_lattice"], "cF")
        # Generic property names
        props = {p["property"] for p in data["results"]["ontology_properties"]}
        self.assertIn("bravais_lattice", props)

    def test_invalid_space_group_exit_code(self):
        result = self.run_cmd([
            str(SCRIPTS / "crystal_mapper.py"),
            "--space-group", "300",
            "--json",
        ])
        self.assertEqual(result.returncode, 2)

    def test_text_output(self):
        result = self.run_cmd([
            str(SCRIPTS / "crystal_mapper.py"),
            "--bravais", "BCC",
            "--a", "2.87",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("cI", result.stdout)


class TestCliSampleAnnotator(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_copper_sample_json(self):
        result = self.run_cmd([
            str(SCRIPTS / "sample_annotator.py"),
            "--ontology", "cmso",
            "--sample",
            '{"material":"copper","structure":"FCC","space_group":225,"lattice_a":3.615}',
            "--json",
        ])
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["results"]["material_type"], "Crystalline Material")
        self.assertIn("annotations", data["results"])

    def test_invalid_sample_exit_code(self):
        result = self.run_cmd([
            str(SCRIPTS / "sample_annotator.py"),
            "--ontology", "cmso",
            "--sample", "not json",
            "--json",
        ])
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
