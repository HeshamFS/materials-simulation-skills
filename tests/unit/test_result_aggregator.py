import json
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestResultAggregator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "result_aggregator",
            "skills/simulation-workflow/simulation-orchestrator/scripts/result_aggregator.py",
        )
        cls.campaign_mod = load_module(
            "campaign_manager",
            "skills/simulation-workflow/simulation-orchestrator/scripts/campaign_manager.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.sweep_dir = os.path.join(self.temp_dir, "sweep")
        os.makedirs(self.sweep_dir)

        # Create manifest
        manifest = {
            "configs": ["config_0000.json", "config_0001.json", "config_0002.json"],
            "parameter_space": {"dt": [0.001, 0.005, 0.01]},
            "sweep_method": "linspace",
            "total_runs": 3,
        }
        with open(os.path.join(self.sweep_dir, "manifest.json"), "w") as f:
            json.dump(manifest, f)

        # Create config files
        for i, config_name in enumerate(manifest["configs"]):
            with open(os.path.join(self.sweep_dir, config_name), "w") as f:
                json.dump({"dt": manifest["parameter_space"]["dt"][i]}, f)

        # Initialize campaign
        self.campaign_mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_extract_metric_simple(self):
        """Test extracting simple metric."""
        result = {"objective": 0.5, "iterations": 100}
        value = self.mod.extract_metric(result, "objective")
        self.assertAlmostEqual(value, 0.5)

    def test_extract_metric_nested(self):
        """Test extracting nested metric."""
        result = {"results": {"energy": 1.5, "mass": 2.0}}
        value = self.mod.extract_metric(result, "results.energy")
        self.assertAlmostEqual(value, 1.5)

    def test_extract_metric_not_found(self):
        """Test extracting non-existent metric."""
        result = {"objective": 0.5}
        value = self.mod.extract_metric(result, "missing")
        self.assertIsNone(value)

    def test_extract_metric_not_numeric(self):
        """Test extracting non-numeric value."""
        result = {"status": "completed"}
        value = self.mod.extract_metric(result, "status")
        self.assertIsNone(value)

    def test_compute_statistics(self):
        """Test statistics computation."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = self.mod.compute_statistics(values)
        self.assertEqual(stats["min"], 1.0)
        self.assertEqual(stats["max"], 5.0)
        self.assertEqual(stats["mean"], 3.0)
        self.assertEqual(stats["median"], 3.0)

    def test_compute_statistics_empty(self):
        """Test statistics for empty list."""
        stats = self.mod.compute_statistics([])
        self.assertIsNone(stats["min"])
        self.assertIsNone(stats["mean"])

    def test_compute_statistics_single(self):
        """Test statistics for single value."""
        stats = self.mod.compute_statistics([5.0])
        self.assertEqual(stats["min"], 5.0)
        self.assertEqual(stats["max"], 5.0)
        self.assertEqual(stats["mean"], 5.0)
        self.assertEqual(stats["std"], 0.0)

    def test_compute_statistics_std(self):
        """Test standard deviation calculation."""
        # Using sample std (n-1 divisor)
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        stats = self.mod.compute_statistics(values)
        self.assertAlmostEqual(stats["mean"], 3.0)
        # Sample std of [1,2,3,4,5] is sqrt(2.5) ≈ 1.58
        self.assertAlmostEqual(stats["std"], 1.5811, places=3)

    def test_aggregate_results_no_results(self):
        """Test aggregation with no result files."""
        results = self.mod.aggregate_results(self.sweep_dir, "objective")
        self.assertEqual(results["summary"]["completed"], 0)
        self.assertIsNone(results["best_run"])

    def test_aggregate_results_with_results(self):
        """Test aggregation with result files."""
        # Create result files
        for i, obj in enumerate([0.5, 0.3, 0.7]):
            result_path = os.path.join(self.sweep_dir, f"result_job_000{i}.json")
            with open(result_path, "w") as f:
                json.dump({"objective": obj}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "objective", minimize=True)
        self.assertEqual(results["summary"]["completed"], 3)
        self.assertEqual(results["best_run"]["job_id"], "job_0001")
        self.assertAlmostEqual(results["best_run"]["value"], 0.3)

    def test_aggregate_results_maximize(self):
        """Test aggregation with maximize."""
        for i, obj in enumerate([0.5, 0.3, 0.7]):
            result_path = os.path.join(self.sweep_dir, f"result_job_000{i}.json")
            with open(result_path, "w") as f:
                json.dump({"objective": obj}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "objective", minimize=False)
        self.assertEqual(results["best_run"]["job_id"], "job_0002")
        self.assertAlmostEqual(results["best_run"]["value"], 0.7)

    def test_aggregate_results_with_failures(self):
        """Test aggregation with failed jobs."""
        # Mark job_0001 as failed
        campaign = self.campaign_mod.load_campaign(self.sweep_dir)
        campaign["jobs"][1]["status"] = "failed"
        self.campaign_mod.save_campaign(self.sweep_dir, campaign)

        # Create result for job_0000 only
        with open(os.path.join(self.sweep_dir, "result_job_0000.json"), "w") as f:
            json.dump({"objective": 0.5}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "objective")
        self.assertEqual(results["summary"]["failed"], 1)
        self.assertIn("job_0001", results["failed_runs"])

    def test_aggregate_results_statistics(self):
        """Test statistics in aggregation."""
        for i, obj in enumerate([1.0, 2.0, 3.0]):
            result_path = os.path.join(self.sweep_dir, f"result_job_000{i}.json")
            with open(result_path, "w") as f:
                json.dump({"objective": obj}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "objective")
        stats = results["statistics"]
        self.assertEqual(stats["min"], 1.0)
        self.assertEqual(stats["max"], 3.0)
        self.assertEqual(stats["mean"], 2.0)

    def test_aggregate_nested_metric(self):
        """Test aggregation with nested metric."""
        for i, val in enumerate([10.0, 20.0, 30.0]):
            result_path = os.path.join(self.sweep_dir, f"result_job_000{i}.json")
            with open(result_path, "w") as f:
                json.dump({"results": {"energy": val}}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "results.energy")
        self.assertEqual(results["summary"]["completed"], 3)
        self.assertEqual(results["statistics"]["min"], 10.0)

    def test_export_table(self):
        """Test CSV export."""
        for i, obj in enumerate([0.5, 0.3, 0.7]):
            result_path = os.path.join(self.sweep_dir, f"result_job_000{i}.json")
            with open(result_path, "w") as f:
                json.dump({"objective": obj}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "objective")
        csv_path = os.path.join(self.temp_dir, "results.csv")
        self.mod.export_table(results, csv_path)

        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path) as f:
            content = f.read()
            self.assertIn("job_id", content)
            self.assertIn("value", content)
            self.assertIn("job_0000", content)

    def test_worst_run(self):
        """Test worst run identification."""
        for i, obj in enumerate([0.5, 0.3, 0.7]):
            result_path = os.path.join(self.sweep_dir, f"result_job_000{i}.json")
            with open(result_path, "w") as f:
                json.dump({"objective": obj}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "objective", minimize=True)
        self.assertEqual(results["worst_run"]["job_id"], "job_0002")
        self.assertAlmostEqual(results["worst_run"]["value"], 0.7)

    def test_all_results_list(self):
        """Test that all_results contains all data."""
        for i, obj in enumerate([0.5, 0.3, 0.7]):
            result_path = os.path.join(self.sweep_dir, f"result_job_000{i}.json")
            with open(result_path, "w") as f:
                json.dump({"objective": obj}, f)

        results = self.mod.aggregate_results(self.sweep_dir, "objective")
        self.assertEqual(len(results["all_results"]), 3)
        job_ids = [r["job_id"] for r in results["all_results"]]
        self.assertIn("job_0000", job_ids)
        self.assertIn("job_0001", job_ids)
        self.assertIn("job_0002", job_ids)


if __name__ == "__main__":
    unittest.main()
