import json
import os
import shutil
import tempfile
import unittest

from tests.unit._utils import load_module


class TestSweepGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "sweep_generator",
            "skills/simulation-workflow/simulation-orchestrator/scripts/sweep_generator.py",
        )

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.base_config_path = os.path.join(self.temp_dir, "base_config.json")
        with open(self.base_config_path, "w") as f:
            json.dump({"solver": "CG", "tolerance": 1e-6}, f)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_parse_param_spec_with_count(self):
        """Test parsing parameter spec with count."""
        name, min_val, max_val, count = self.mod.parse_param_spec("dt:0.001:0.01:5")
        self.assertEqual(name, "dt")
        self.assertAlmostEqual(min_val, 0.001)
        self.assertAlmostEqual(max_val, 0.01)
        self.assertEqual(count, 5)

    def test_parse_param_spec_without_count(self):
        """Test parsing parameter spec without count (for LHS)."""
        name, min_val, max_val, count = self.mod.parse_param_spec("kappa:0.1:1.0")
        self.assertEqual(name, "kappa")
        self.assertAlmostEqual(min_val, 0.1)
        self.assertAlmostEqual(max_val, 1.0)
        self.assertEqual(count, -1)

    def test_parse_params_multiple(self):
        """Test parsing multiple parameter specs."""
        params = self.mod.parse_params("dt:0.001:0.01:5,kappa:0.1:1.0:3")
        self.assertEqual(len(params), 2)
        self.assertEqual(params[0][0], "dt")
        self.assertEqual(params[1][0], "kappa")

    def test_linspace(self):
        """Test linspace generation."""
        values = self.mod.linspace(0.0, 1.0, 5)
        self.assertEqual(len(values), 5)
        self.assertAlmostEqual(values[0], 0.0)
        self.assertAlmostEqual(values[-1], 1.0)
        self.assertAlmostEqual(values[2], 0.5)

    def test_linspace_single(self):
        """Test linspace with single point."""
        values = self.mod.linspace(0.5, 1.0, 1)
        self.assertEqual(len(values), 1)
        self.assertAlmostEqual(values[0], 0.5)

    def test_generate_grid(self):
        """Test grid generation."""
        params = [("dt", 0.001, 0.01, 3), ("kappa", 0.1, 1.0, 2)]
        configs = self.mod.generate_grid(params)
        self.assertEqual(len(configs), 6)  # 3 x 2
        self.assertIn("dt", configs[0])
        self.assertIn("kappa", configs[0])

    def test_generate_lhs(self):
        """Test LHS generation."""
        params = [("dt", 0.001, 0.01, -1), ("kappa", 0.1, 1.0, -1)]
        configs, param_space = self.mod.generate_lhs(params, samples=10, seed=42)
        self.assertEqual(len(configs), 10)
        self.assertEqual(len(param_space["dt"]), 10)
        self.assertEqual(len(param_space["kappa"]), 10)
        # Check values are in range
        for config in configs:
            self.assertGreaterEqual(config["dt"], 0.001)
            self.assertLessEqual(config["dt"], 0.01)
            self.assertGreaterEqual(config["kappa"], 0.1)
            self.assertLessEqual(config["kappa"], 1.0)

    def test_generate_lhs_reproducible(self):
        """Test LHS is reproducible with same seed."""
        params = [("dt", 0.001, 0.01, -1)]
        configs1, _ = self.mod.generate_lhs(params, samples=5, seed=42)
        configs2, _ = self.mod.generate_lhs(params, samples=5, seed=42)
        self.assertEqual(configs1, configs2)

    def test_merge_config(self):
        """Test config merging."""
        base = {"solver": "CG", "tolerance": 1e-6}
        overrides = {"dt": 0.001, "tolerance": 1e-8}
        merged = self.mod.merge_config(base, overrides)
        self.assertEqual(merged["solver"], "CG")
        self.assertEqual(merged["dt"], 0.001)
        self.assertEqual(merged["tolerance"], 1e-8)

    def test_generate_sweep_linspace(self):
        """Test full sweep generation with linspace."""
        output_dir = os.path.join(self.temp_dir, "sweep_001")
        result = self.mod.generate_sweep(
            base_config_path=self.base_config_path,
            params_str="dt:0.001:0.01:3",
            method="linspace",
            output_dir=output_dir,
        )
        self.assertEqual(result["total_runs"], 3)
        self.assertEqual(result["sweep_method"], "linspace")
        self.assertEqual(len(result["configs"]), 3)
        # Check files exist
        self.assertTrue(os.path.exists(os.path.join(output_dir, "config_0000.json")))
        self.assertTrue(os.path.exists(os.path.join(output_dir, "manifest.json")))

    def test_generate_sweep_grid_2d(self):
        """Test 2D grid sweep."""
        output_dir = os.path.join(self.temp_dir, "sweep_002")
        result = self.mod.generate_sweep(
            base_config_path=self.base_config_path,
            params_str="dt:0.001:0.01:2,kappa:0.1:1.0:3",
            method="grid",
            output_dir=output_dir,
        )
        self.assertEqual(result["total_runs"], 6)  # 2 x 3

    def test_generate_sweep_lhs(self):
        """Test LHS sweep."""
        output_dir = os.path.join(self.temp_dir, "sweep_003")
        result = self.mod.generate_sweep(
            base_config_path=self.base_config_path,
            params_str="dt:0.001:0.01,kappa:0.1:1.0",
            method="lhs",
            output_dir=output_dir,
            samples=15,
        )
        self.assertEqual(result["total_runs"], 15)

    def test_base_config_not_found(self):
        """Test error when base config doesn't exist."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.generate_sweep(
                base_config_path="/nonexistent/config.json",
                params_str="dt:0.001:0.01:3",
                method="linspace",
                output_dir=os.path.join(self.temp_dir, "sweep_err"),
            )
        self.assertIn("not found", str(ctx.exception))

    def test_output_dir_exists_without_force(self):
        """Test error when output directory exists without --force."""
        output_dir = os.path.join(self.temp_dir, "existing")
        os.makedirs(output_dir)
        with self.assertRaises(ValueError) as ctx:
            self.mod.generate_sweep(
                base_config_path=self.base_config_path,
                params_str="dt:0.001:0.01:3",
                method="linspace",
                output_dir=output_dir,
            )
        self.assertIn("exists", str(ctx.exception))

    def test_output_dir_exists_with_force(self):
        """Test overwrite when --force is used."""
        output_dir = os.path.join(self.temp_dir, "existing2")
        os.makedirs(output_dir)
        result = self.mod.generate_sweep(
            base_config_path=self.base_config_path,
            params_str="dt:0.001:0.01:3",
            method="linspace",
            output_dir=output_dir,
            force=True,
        )
        self.assertEqual(result["total_runs"], 3)

    def test_invalid_method(self):
        """Test error for invalid method."""
        with self.assertRaises(ValueError) as ctx:
            self.mod.generate_sweep(
                base_config_path=self.base_config_path,
                params_str="dt:0.001:0.01:3",
                method="invalid",
                output_dir=os.path.join(self.temp_dir, "sweep_inv"),
            )
        self.assertIn("Unknown method", str(ctx.exception))

    def test_merge_config_deep_copy(self):
        """merge_config must deep-copy nested dicts to prevent cross-contamination."""
        base = {"solver": "CG", "nested": {"a": 1, "b": [2, 3]}}
        overrides = {"dt": 0.001}
        merged = self.mod.merge_config(base, overrides)
        # Mutating the merged dict must not affect base
        merged["nested"]["a"] = 999
        merged["nested"]["b"].append(4)
        self.assertEqual(base["nested"]["a"], 1)
        self.assertEqual(base["nested"]["b"], [2, 3])

    def test_parse_param_spec_min_greater_than_max_raises(self):
        """Reversed range (min > max) must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.parse_param_spec("dt:0.01:0.001:5")

    def test_parse_param_spec_equal_min_max_raises(self):
        """Equal min and max must raise ValueError."""
        with self.assertRaises(ValueError):
            self.mod.parse_param_spec("dt:0.01:0.01:5")

    def test_config_content(self):
        """Test generated config file content."""
        output_dir = os.path.join(self.temp_dir, "sweep_content")
        self.mod.generate_sweep(
            base_config_path=self.base_config_path,
            params_str="dt:0.001:0.01:2",
            method="linspace",
            output_dir=output_dir,
        )
        config_path = os.path.join(output_dir, "config_0000.json")
        with open(config_path) as f:
            config = json.load(f)
        self.assertEqual(config["solver"], "CG")  # From base
        self.assertIn("dt", config)  # From sweep


if __name__ == "__main__":
    unittest.main()
