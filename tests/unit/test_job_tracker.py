import json
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestJobTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "job_tracker",
            "skills/simulation-workflow/simulation-orchestrator/scripts/job_tracker.py",
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
        for config_name in manifest["configs"]:
            with open(os.path.join(self.sweep_dir, config_name), "w") as f:
                json.dump({"dt": 0.001}, f)

        # Initialize campaign
        self.campaign_mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_load_campaign(self):
        """Test campaign loading."""
        campaign = self.mod.load_campaign(self.sweep_dir)
        self.assertEqual(len(campaign["jobs"]), 3)

    def test_get_job_info(self):
        """Test getting specific job info."""
        job = self.mod.get_job_info(self.sweep_dir, "job_0001")
        self.assertEqual(job["job_id"], "job_0001")
        self.assertEqual(job["status"], "pending")

    def test_get_job_info_not_found(self):
        """Test error when job not found."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.get_job_info(self.sweep_dir, "job_9999")
        self.assertIn("not found", str(ctx.exception))

    def test_mark_job_status_running(self):
        """Test marking job as running."""
        job = self.mod.mark_job_status(self.sweep_dir, "job_0000", "running")
        self.assertEqual(job["status"], "running")
        self.assertIsNotNone(job["start_time"])

    def test_mark_job_status_completed(self):
        """Test marking job as completed."""
        job = self.mod.mark_job_status(self.sweep_dir, "job_0000", "completed", exit_code=0)
        self.assertEqual(job["status"], "completed")
        self.assertIsNotNone(job["end_time"])
        self.assertEqual(job["exit_code"], 0)

    def test_mark_job_status_failed(self):
        """Test marking job as failed."""
        job = self.mod.mark_job_status(self.sweep_dir, "job_0000", "failed", exit_code=1)
        self.assertEqual(job["status"], "failed")
        self.assertEqual(job["exit_code"], 1)

    def test_mark_job_status_invalid(self):
        """Test error for invalid status."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.mark_job_status(self.sweep_dir, "job_0000", "invalid")
        self.assertIn("Invalid status", str(ctx.exception))

    def test_detect_job_status_pending(self):
        """Test status detection for pending job (no files)."""
        campaign = self.mod.load_campaign(self.sweep_dir)
        job = campaign["jobs"][0]
        updated = self.mod.detect_job_status(job, self.sweep_dir)
        self.assertEqual(updated["status"], "pending")

    def test_detect_job_status_completed(self):
        """Test status detection from result file."""
        # Create result file
        result_path = os.path.join(self.sweep_dir, "result_job_0000.json")
        with open(result_path, "w") as f:
            json.dump({"objective": 0.5}, f)

        campaign = self.mod.load_campaign(self.sweep_dir)
        job = campaign["jobs"][0]
        updated = self.mod.detect_job_status(job, self.sweep_dir)
        self.assertEqual(updated["status"], "completed")

    def test_detect_job_status_failed(self):
        """Test status detection from error file."""
        # Create error file
        error_path = os.path.join(self.sweep_dir, "error_job_0001.log")
        with open(error_path, "w") as f:
            f.write("Simulation failed")

        campaign = self.mod.load_campaign(self.sweep_dir)
        job = campaign["jobs"][1]
        updated = self.mod.detect_job_status(job, self.sweep_dir)
        self.assertEqual(updated["status"], "failed")

    def test_detect_job_status_running(self):
        """Test status detection from running marker."""
        # Create running marker
        running_path = os.path.join(self.sweep_dir, "job_0002.running")
        with open(running_path, "w") as f:
            f.write("")

        campaign = self.mod.load_campaign(self.sweep_dir)
        job = campaign["jobs"][2]
        updated = self.mod.detect_job_status(job, self.sweep_dir)
        self.assertEqual(updated["status"], "running")

    def test_update_all_jobs(self):
        """Test updating all jobs."""
        # Create result file for job_0000
        result_path = os.path.join(self.sweep_dir, "result_job_0000.json")
        with open(result_path, "w") as f:
            json.dump({"objective": 0.5}, f)

        result = self.mod.update_all_jobs(self.sweep_dir)
        self.assertEqual(result["changes"]["updated"], 1)
        self.assertEqual(result["status_counts"]["completed"], 1)
        self.assertEqual(result["status_counts"]["pending"], 2)

    def test_update_all_jobs_multiple(self):
        """Test updating multiple jobs."""
        # Create result for job_0000
        with open(os.path.join(self.sweep_dir, "result_job_0000.json"), "w") as f:
            json.dump({"objective": 0.5}, f)
        # Create error for job_0001
        with open(os.path.join(self.sweep_dir, "error_job_0001.log"), "w") as f:
            f.write("Error")

        result = self.mod.update_all_jobs(self.sweep_dir)
        self.assertEqual(result["status_counts"]["completed"], 1)
        self.assertEqual(result["status_counts"]["failed"], 1)
        self.assertEqual(result["status_counts"]["pending"], 1)

    def test_status_persistence(self):
        """Test that status changes are persisted."""
        self.mod.mark_job_status(self.sweep_dir, "job_0000", "completed")
        # Reload and verify
        job = self.mod.get_job_info(self.sweep_dir, "job_0000")
        self.assertEqual(job["status"], "completed")

    def test_custom_result_pattern(self):
        """Test detection with custom result pattern."""
        # Create result with custom pattern
        with open(os.path.join(self.sweep_dir, "output_job_0000.json"), "w") as f:
            json.dump({"value": 1.0}, f)

        campaign = self.mod.load_campaign(self.sweep_dir)
        job = campaign["jobs"][0]
        updated = self.mod.detect_job_status(
            job, self.sweep_dir, result_pattern="output_{job_id}.json"
        )
        self.assertEqual(updated["status"], "completed")


if __name__ == "__main__":
    unittest.main()
