"""Unit tests for post-processing field_extractor.py script."""

import json
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestFieldExtractor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "field_extractor",
            "skills/simulation-workflow/post-processing/scripts/field_extractor.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_flatten_list_1d(self):
        """Test flattening 1D list."""
        result = self.mod.flatten_list([1, 2, 3, 4])
        self.assertEqual(result, [1, 2, 3, 4])

    def test_flatten_list_2d(self):
        """Test flattening 2D list."""
        result = self.mod.flatten_list([[1, 2], [3, 4]])
        self.assertEqual(result, [1, 2, 3, 4])

    def test_flatten_list_mixed(self):
        """Test flattening mixed nested list."""
        result = self.mod.flatten_list([1, [2, 3], [[4]]])
        self.assertEqual(result, [1, 2, 3, 4])

    def test_get_shape_1d(self):
        """Test getting shape of 1D list."""
        result = self.mod.get_shape([1, 2, 3, 4])
        self.assertEqual(result, [4])

    def test_get_shape_2d(self):
        """Test getting shape of 2D list."""
        result = self.mod.get_shape([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(result, [2, 3])

    def test_get_shape_3d(self):
        """Test getting shape of 3D list."""
        result = self.mod.get_shape([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
        self.assertEqual(result, [2, 2, 2])

    def test_list_available_fields(self):
        """Test listing available fields."""
        data = {"phi": [1, 2, 3], "concentration": [4, 5, 6], "scalar": 1.0}
        result = self.mod.list_available_fields(data)
        self.assertIn("phi", result)
        self.assertIn("concentration", result)

    def test_extract_field_simple(self):
        """Test extracting simple field."""
        data = {"phi": [0.0, 0.5, 1.0]}
        result = self.mod.extract_field(data, "phi")
        self.assertTrue(result["found"])
        self.assertEqual(result["field"], "phi")
        self.assertEqual(result["min"], 0.0)
        self.assertEqual(result["max"], 1.0)

    def test_extract_field_2d(self):
        """Test extracting 2D field."""
        data = {"phi": [[0.0, 0.5], [0.5, 1.0]]}
        result = self.mod.extract_field(data, "phi")
        self.assertTrue(result["found"])
        self.assertEqual(result["shape"], [2, 2])
        self.assertEqual(result["min"], 0.0)
        self.assertEqual(result["max"], 1.0)

    def test_extract_field_not_found(self):
        """Test extracting non-existent field."""
        data = {"phi": [1, 2, 3]}
        result = self.mod.extract_field(data, "missing")
        self.assertIsNone(result)

    def test_extract_field_from_data_key(self):
        """Test extracting field from _data key."""
        data = {"_data": {"phi": [0.1, 0.2, 0.3]}}
        result = self.mod.extract_field(data, "phi")
        self.assertTrue(result["found"])

    def test_extract_multiple_fields(self):
        """Test extracting multiple fields."""
        data = {"phi": [0.0, 1.0], "c": [0.5, 0.5]}
        result = self.mod.extract_multiple_fields(data, ["phi", "c"])
        self.assertIn("phi", result["fields"])
        self.assertIn("c", result["fields"])
        self.assertTrue(result["fields"]["phi"]["found"])

    def test_extract_multiple_fields_partial(self):
        """Test extracting multiple fields with some missing."""
        data = {"phi": [0.0, 1.0]}
        result = self.mod.extract_multiple_fields(data, ["phi", "missing"])
        self.assertTrue(result["fields"]["phi"]["found"])
        self.assertFalse(result["fields"]["missing"]["found"])

    def test_get_timestep_info(self):
        """Test extracting timestep info."""
        data = {"timestep": 100, "time": 0.5, "phi": [1, 2, 3]}
        result = self.mod.get_timestep_info(data)
        self.assertEqual(result["timestep"], 100)
        self.assertEqual(result["time"], 0.5)

    def test_get_timestep_info_none(self):
        """Test extracting timestep info when none present."""
        data = {"phi": [1, 2, 3]}
        result = self.mod.get_timestep_info(data)
        self.assertIsNone(result)

    def test_load_json_file(self):
        """Test loading JSON file."""
        filepath = os.path.join(self.temp_dir, "test.json")
        data = {"phi": [1, 2, 3], "value": 0.5}
        with open(filepath, "w") as f:
            json.dump(data, f)

        result = self.mod.load_json_file(filepath)
        self.assertEqual(result["phi"], [1, 2, 3])
        self.assertEqual(result["value"], 0.5)

    def test_load_csv_file(self):
        """Test loading CSV file."""
        filepath = os.path.join(self.temp_dir, "test.csv")
        with open(filepath, "w") as f:
            f.write("x,y,z\n")
            f.write("1,2,3\n")
            f.write("4,5,6\n")

        result = self.mod.load_csv_file(filepath)
        self.assertIn("_data", result)
        self.assertEqual(result["_data"]["x"], [1.0, 4.0])
        self.assertEqual(result["_data"]["y"], [2.0, 5.0])

    def test_list_available_files(self):
        """Test listing files in directory."""
        # Create test files
        for name in ["field_0001.json", "field_0002.json", "data.csv"]:
            with open(os.path.join(self.temp_dir, name), "w") as f:
                f.write("{}" if name.endswith(".json") else "x,y\n")

        result = self.mod.list_available_files(self.temp_dir)
        self.assertEqual(len(result), 3)
        filenames = [f["filename"] for f in result]
        self.assertIn("field_0001.json", filenames)


class TestFieldExtractorEdgeCases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "field_extractor",
            "skills/simulation-workflow/post-processing/scripts/field_extractor.py",
        )

    def test_flatten_empty(self):
        """Test flattening empty list."""
        result = self.mod.flatten_list([])
        self.assertEqual(result, [])

    def test_flatten_scalar(self):
        """Test flattening scalar."""
        result = self.mod.flatten_list(5.0)
        self.assertEqual(result, [5.0])

    def test_flatten_non_numeric(self):
        """Test flattening non-numeric values."""
        result = self.mod.flatten_list(["a", "b"])
        self.assertEqual(result, [])

    def test_get_shape_empty(self):
        """Test getting shape of empty list."""
        result = self.mod.get_shape([])
        self.assertEqual(result, [0])

    def test_extract_field_statistics(self):
        """Test field statistics computation."""
        data = {"phi": [1, 2, 3, 4, 5]}
        result = self.mod.extract_field(data, "phi")
        self.assertEqual(result["mean"], 3.0)
        self.assertEqual(result["count"], 5)


if __name__ == "__main__":
    unittest.main()
