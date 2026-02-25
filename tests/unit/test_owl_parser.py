"""Unit tests for owl_parser.py."""

import os
import tempfile
import unittest

from tests.unit._utils import load_module

OWL_PARSER = load_module(
    "owl_parser",
    "skills/ontology/ontology-explorer/scripts/owl_parser.py",
)

MINIMAL_OWL = """\
<?xml version="1.0"?>
<rdf:RDF xmlns="http://example.org/test#"
     xml:base="http://example.org/test"
     xmlns:owl="http://www.w3.org/2002/07/owl#"
     xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
     xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#"
     xmlns:xsd="http://www.w3.org/2001/XMLSchema#"
     xmlns:dc="http://purl.org/dc/elements/1.1/">
    <owl:Ontology rdf:about="http://example.org/test">
        <owl:versionInfo>1.0.0</owl:versionInfo>
        <dc:title>Test Ontology</dc:title>
    </owl:Ontology>
    <owl:Class rdf:about="http://example.org/test#Animal">
        <rdfs:label>Animal</rdfs:label>
        <rdfs:comment>A living organism</rdfs:comment>
    </owl:Class>
    <owl:Class rdf:about="http://example.org/test#Dog">
        <rdfs:label>Dog</rdfs:label>
        <rdfs:subClassOf rdf:resource="http://example.org/test#Animal"/>
    </owl:Class>
    <owl:Class rdf:about="http://example.org/test#Cat">
        <rdfs:label>Cat</rdfs:label>
        <rdfs:subClassOf rdf:resource="http://example.org/test#Animal"/>
    </owl:Class>
    <owl:ObjectProperty rdf:about="http://example.org/test#hasOwner">
        <rdfs:label>has owner</rdfs:label>
        <rdfs:domain rdf:resource="http://example.org/test#Animal"/>
        <rdfs:range rdf:resource="http://example.org/test#Person"/>
    </owl:ObjectProperty>
    <owl:DatatypeProperty rdf:about="http://example.org/test#hasName">
        <rdfs:label>has name</rdfs:label>
        <rdfs:domain rdf:resource="http://example.org/test#Animal"/>
        <rdfs:range rdf:resource="http://www.w3.org/2001/XMLSchema#string"/>
    </owl:DatatypeProperty>
</rdf:RDF>
"""


class TestOwlParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.NamedTemporaryFile(
            suffix=".owl", mode="w", delete=False, encoding="utf-8",
        )
        cls.tmp.write(MINIMAL_OWL)
        cls.tmp.close()
        cls.result = OWL_PARSER.parse_owl(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.tmp.name)

    def test_metadata(self):
        m = self.result["metadata"]
        self.assertEqual(m["iri"], "http://example.org/test")
        self.assertEqual(m["version"], "1.0.0")
        self.assertEqual(m["title"], "Test Ontology")

    def test_classes_count(self):
        self.assertEqual(len(self.result["classes"]), 3)

    def test_class_labels(self):
        labels = {c["label"] for c in self.result["classes"]}
        self.assertEqual(labels, {"Animal", "Dog", "Cat"})

    def test_class_hierarchy(self):
        dog = [c for c in self.result["classes"] if c["label"] == "Dog"][0]
        self.assertEqual(dog["parent"], "Animal")

    def test_class_description(self):
        animal = [c for c in self.result["classes"] if c["label"] == "Animal"][0]
        self.assertEqual(animal["description"], "A living organism")

    def test_object_properties(self):
        self.assertEqual(len(self.result["object_properties"]), 1)
        prop = self.result["object_properties"][0]
        self.assertEqual(prop["label"], "has owner")
        self.assertEqual(prop["domain"], "Animal")
        self.assertEqual(prop["range"], "Person")

    def test_data_properties(self):
        self.assertEqual(len(self.result["data_properties"]), 1)
        prop = self.result["data_properties"][0]
        self.assertEqual(prop["label"], "has name")
        self.assertEqual(prop["domain"], "Animal")
        self.assertEqual(prop["range_type"], "string")

    def test_class_hierarchy_tree(self):
        tree = self.result["class_hierarchy"]
        self.assertIn("Animal", tree)
        self.assertIn("Cat", tree["Animal"])
        self.assertIn("Dog", tree["Animal"])

    def test_invalid_source_raises(self):
        with self.assertRaises(ValueError):
            OWL_PARSER.parse_owl("/nonexistent/file.owl")

    def test_malformed_xml_raises(self):
        tmp = tempfile.NamedTemporaryFile(
            suffix=".owl", mode="w", delete=False, encoding="utf-8",
        )
        tmp.write("<not valid xml")
        tmp.close()
        try:
            with self.assertRaises(ValueError):
                OWL_PARSER.parse_owl(tmp.name)
        finally:
            os.unlink(tmp.name)

    def test_nan_not_in_output(self):
        """Ensure no NaN values appear in parsed output."""
        import json
        text = json.dumps(self.result)
        self.assertNotIn("NaN", text)


if __name__ == "__main__":
    unittest.main()
