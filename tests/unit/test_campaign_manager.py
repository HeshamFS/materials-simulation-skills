import json
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestCampaignManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "campaign_manager",
            "skills/simulation-workflow/simulation-orchestrator/scripts/campaign_manager.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Create a mock sweep directory with manifest
        self.sweep_dir = os.path.join(self.temp_dir, "sweep")
        os.makedirs(self.sweep_dir)

        self.manifest = {
            "configs": ["config_0000.json", "config_0001.json", "config_0002.json"],
            "parameter_space": {"dt": [0.001, 0.005, 0.01]},
            "sweep_method": "linspace",
            "total_runs": 3,
        }
        with open(os.path.join(self.sweep_dir, "manifest.json"), "w") as f:
            json.dump(self.manifest, f)

        # Create config files
        for i, config_name in enumerate(self.manifest["configs"]):
            config_path = os.path.join(self.sweep_dir, config_name)
            with open(config_path, "w") as f:
                json.dump({"dt": self.manifest["parameter_space"]["dt"][i]}, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_generate_campaign_id(self):
        """Test campaign ID generation."""
        id1 = self.mod.generate_campaign_id()
        id2 = self.mod.generate_campaign_id()
        self.assertTrue(id1.startswith("campaign_"))
        self.assertNotEqual(id1, id2)

    def test_load_manifest(self):
        """Test manifest loading."""
        manifest = self.mod.load_manifest(self.sweep_dir)
        self.assertEqual(manifest["total_runs"], 3)
        self.assertEqual(len(manifest["configs"]), 3)

    def test_load_manifest_not_found(self):
        """Test error when manifest not found."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.load_manifest("/nonexistent/path")
        self.assertIn("not found", str(ctx.exception))

    def test_init_campaign(self):
        """Test campaign initialization."""
        campaign = self.mod.init_campaign(
            config_dir=self.sweep_dir,
            command_template="python sim.py --config {config}",
        )
        self.assertIn("campaign_id", campaign)
        self.assertEqual(len(campaign["jobs"]), 3)
        for job in campaign["jobs"]:
            self.assertEqual(job["status"], "pending")
            self.assertIn("python sim.py", job["command"])

    def test_init_creates_campaign_file(self):
        """Test that init creates campaign.json."""
        self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        campaign_path = os.path.join(self.sweep_dir, "campaign.json")
        self.assertTrue(os.path.exists(campaign_path))

    def test_get_campaign_status_not_started(self):
        """Test status when no jobs have run."""
        self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        status = self.mod.get_campaign_status(self.sweep_dir)
        self.assertEqual(status["status"], "not_started")
        self.assertEqual(status["jobs"]["pending"], 3)
        self.assertEqual(status["progress"], 0.0)

    def test_get_campaign_status_in_progress(self):
        """Test status when some jobs are running/completed."""
        campaign = self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        # Modify some jobs
        campaign["jobs"][0]["status"] = "completed"
        campaign["jobs"][1]["status"] = "running"
        self.mod.save_campaign(self.sweep_dir, campaign)

        status = self.mod.get_campaign_status(self.sweep_dir)
        self.assertEqual(status["status"], "in_progress")
        self.assertEqual(status["jobs"]["completed"], 1)
        self.assertEqual(status["jobs"]["running"], 1)
        self.assertEqual(status["jobs"]["pending"], 1)

    def test_get_campaign_status_completed(self):
        """Test status when all jobs completed."""
        campaign = self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        for job in campaign["jobs"]:
            job["status"] = "completed"
        self.mod.save_campaign(self.sweep_dir, campaign)

        status = self.mod.get_campaign_status(self.sweep_dir)
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["progress"], 1.0)

    def test_get_campaign_status_with_failures(self):
        """Test status when some jobs failed."""
        campaign = self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        campaign["jobs"][0]["status"] = "completed"
        campaign["jobs"][1]["status"] = "completed"
        campaign["jobs"][2]["status"] = "failed"
        self.mod.save_campaign(self.sweep_dir, campaign)

        status = self.mod.get_campaign_status(self.sweep_dir)
        self.assertEqual(status["status"], "completed_with_failures")
        self.assertEqual(status["jobs"]["failed"], 1)

    def test_list_jobs_all(self):
        """Test listing all jobs."""
        self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        jobs = self.mod.list_jobs(self.sweep_dir)
        self.assertEqual(len(jobs), 3)

    def test_list_jobs_filtered(self):
        """Test listing jobs with status filter."""
        campaign = self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        campaign["jobs"][0]["status"] = "completed"
        self.mod.save_campaign(self.sweep_dir, campaign)

        pending = self.mod.list_jobs(self.sweep_dir, status_filter="pending")
        self.assertEqual(len(pending), 2)

        completed = self.mod.list_jobs(self.sweep_dir, status_filter="completed")
        self.assertEqual(len(completed), 1)

    def test_job_command_substitution(self):
        """Test that {config} is replaced in command."""
        campaign = self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        job = campaign["jobs"][0]
        self.assertNotIn("{config}", job["command"])
        self.assertIn("config_0000.json", job["command"])

    def test_load_campaign_not_initialized(self):
        """Test error when campaign not initialized."""
        new_dir = os.path.join(self.temp_dir, "no_campaign")
        os.makedirs(new_dir)
        with open(os.path.join(new_dir, "manifest.json"), "w") as f:
            json.dump(self.manifest, f)

        with self.assertRaises(ValueError) as ctx:
            self.mod.load_campaign(new_dir)
        self.assertIn("not initialized", str(ctx.exception))

    def test_progress_calculation(self):
        """Test progress percentage calculation."""
        campaign = self.mod.init_campaign(self.sweep_dir, "python sim.py --config {config}")
        campaign["jobs"][0]["status"] = "completed"
        self.mod.save_campaign(self.sweep_dir, campaign)

        status = self.mod.get_campaign_status(self.sweep_dir)
        self.assertAlmostEqual(status["progress"], 1/3, places=4)


if __name__ == "__main__":
    unittest.main()
