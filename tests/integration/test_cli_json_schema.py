import json
import subprocess
import sys
import unittest
from pathlib import Path

from tests.integration._schema import assert_schema


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "core-numerical" / "numerical-stability" / "scripts"


class TestCliJsonSchema(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_cfl_schema(self):
        cmd = [
            str(SCRIPTS / "cfl_checker.py"),
            "--dx",
            "0.1",
            "--dt",
            "0.01",
            "--velocity",
            "1.0",
            "--diffusivity",
            "0.1",
            "--reaction-rate",
            "2.0",
            "--dimensions",
            "2",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "dx": (int, float),
                    "dt": (int, float),
                    "velocity": (type(None), int, float),
                    "diffusivity": (type(None), int, float),
                    "reaction_rate": (type(None), int, float),
                    "dimensions": int,
                    "scheme": str,
                    "safety": (int, float),
                },
                "metrics": {
                    "cfl": (type(None), int, float),
                    "fourier": (type(None), int, float),
                    "reaction": (type(None), int, float),
                },
                "limits": {
                    "advection_limit": (int, float),
                    "diffusion_limit": (int, float),
                    "reaction_limit": (int, float),
                },
                "criteria_applied": [str],
                "recommended_dt": (type(None), int, float),
                "stable": (type(None), bool),
                "notes": [str],
            },
        )

    def test_von_neumann_schema(self):
        cmd = [
            str(SCRIPTS / "von_neumann_analyzer.py"),
            "--coeffs",
            "0.2,0.6,0.2",
            "--nk",
            "64",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "coeffs": [float],
                    "dx": (int, float),
                    "kmin": (int, float),
                    "kmax": (int, float),
                    "nk": int,
                    "offset": int,
                },
                "results": {
                    "max_amplification": (int, float),
                    "k_at_max": (int, float),
                    "stable": bool,
                    "warning": (type(None), str),
                },
            },
        )

    def test_matrix_condition_schema(self):
        matrix_path = ROOT / "tests" / "integration" / "schema_matrix.txt"
        matrix_path.write_text("1 0\n0 2\n")
        try:
            cmd = [
                str(SCRIPTS / "matrix_condition.py"),
                "--matrix",
                str(matrix_path),
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {
                        "matrix": str,
                        "shape": [int],
                        "norm": str,
                        "symmetry_tol": (int, float),
                        "skip_eigs": bool,
                    },
                    "results": {
                        "condition_number": (int, float),
                        "eigenvalue_spread": (type(None), int, float),
                        "eigenvalue_min_abs": (type(None), int, float),
                        "eigenvalue_max_abs": (type(None), int, float),
                        "is_symmetric": bool,
                        "status": str,
                        "note": (type(None), str),
                    },
                },
            )
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_stiffness_schema(self):
        cmd = [
            str(SCRIPTS / "stiffness_detector.py"),
            "--eigs=-1,-1000",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {"source": str, "threshold": (int, float)},
                "results": {
                    "stiffness_ratio": (int, float),
                    "stiff": bool,
                    "recommendation": str,
                    "nonzero_count": int,
                    "total_count": int,
                },
            },
        )

    def test_error_norm_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "numerical-integration"
                / "scripts"
                / "error_norm.py"
            ),
            "--error",
            "0.1,0.2",
            "--solution",
            "1.0,2.0",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "error": [float],
                    "solution": (type(None), list),
                    "scale": (type(None), list),
                    "rtol": (int, float),
                    "atol": (int, float),
                    "norm": str,
                    "min_scale": (int, float),
                },
                "results": {
                    "error_norm": (int, float),
                    "max_component": (int, float),
                    "scale_min": (int, float),
                    "scale_max": (int, float),
                },
            },
        )

    def test_adaptive_step_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "numerical-integration"
                / "scripts"
                / "adaptive_step_controller.py"
            ),
            "--dt",
            "0.1",
            "--error-norm",
            "0.5",
            "--order",
            "4",
            "--controller",
            "pi",
            "--prev-error",
            "0.6",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "dt": (int, float),
                    "error_norm": (int, float),
                    "order": int,
                    "accept_threshold": (int, float),
                    "safety": (int, float),
                    "min_factor": (int, float),
                    "max_factor": (int, float),
                    "controller": str,
                    "prev_error": (type(None), int, float),
                },
                "results": {
                    "accept": bool,
                    "dt_next": (int, float),
                    "factor": (int, float),
                    "controller_used": str,
                    "note": (type(None), str),
                },
            },
        )

    def test_integrator_selector_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "numerical-integration"
                / "scripts"
                / "integrator_selector.py"
            ),
            "--stiff",
            "--jacobian-available",
            "--implicit-allowed",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "stiff": bool,
                    "oscillatory": bool,
                    "event_detection": bool,
                    "jacobian_available": bool,
                    "implicit_allowed": bool,
                    "accuracy": str,
                    "dimension": int,
                    "low_memory": bool,
                },
                "results": {
                    "recommended": [str],
                    "alternatives": [str],
                    "notes": [str],
                },
            },
        )

    def test_imex_split_planner_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "numerical-integration"
                / "scripts"
                / "imex_split_planner.py"
            ),
            "--stiff-terms",
            "diffusion,elastic",
            "--nonstiff-terms",
            "reaction",
            "--coupling",
            "strong",
            "--accuracy",
            "high",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "stiff_terms": [str],
                    "nonstiff_terms": [str],
                    "coupling": str,
                    "accuracy": str,
                    "stiffness_ratio": (int, float),
                    "conservative": bool,
                },
                "results": {
                    "implicit_terms": [str],
                    "explicit_terms": [str],
                    "recommended_integrator": [str],
                    "splitting_strategy": str,
                    "notes": [str],
                },
            },
        )

    def test_splitting_error_estimator_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "numerical-integration"
                / "scripts"
                / "splitting_error_estimator.py"
            ),
            "--dt",
            "1e-3",
            "--scheme",
            "strang",
            "--commutator-norm",
            "100",
            "--target-error",
            "1e-6",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "dt": (int, float),
                    "scheme": str,
                    "commutator_norm": (int, float),
                    "target_error": (int, float),
                },
                "results": {
                    "scheme": str,
                    "order": int,
                    "error_estimate": (int, float),
                    "dt_effective": (int, float),
                    "substeps": int,
                },
            },
        )

    def test_timestep_planner_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "time-stepping"
                / "scripts"
                / "timestep_planner.py"
            ),
            "--dt-target",
            "1e-4",
            "--dt-limit",
            "2e-4",
            "--safety",
            "0.8",
            "--ramp-steps",
            "5",
            "--preview-steps",
            "3",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "dt_target": (int, float),
                    "dt_limit": (int, float),
                    "safety": (int, float),
                    "dt_min": (type(None), int, float),
                    "dt_max": (type(None), int, float),
                    "ramp_steps": int,
                    "ramp_kind": str,
                    "preview_steps": int,
                },
                "results": {
                    "dt_limit": (int, float),
                    "dt_recommended": (int, float),
                    "ramp_schedule": [float],
                    "notes": [str],
                },
            },
        )

    def test_output_schedule_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "time-stepping"
                / "scripts"
                / "output_schedule.py"
            ),
            "--t-start",
            "0",
            "--t-end",
            "1",
            "--interval",
            "0.2",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "t_start": (int, float),
                    "t_end": (int, float),
                    "interval": (int, float),
                    "max_outputs": int,
                },
                "results": {
                    "interval": (int, float),
                    "count": int,
                    "output_times": [float],
                },
            },
        )

    def test_checkpoint_planner_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "time-stepping"
                / "scripts"
                / "checkpoint_planner.py"
            ),
            "--run-time",
            "36000",
            "--checkpoint-cost",
            "120",
            "--max-lost-time",
            "1800",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "run_time": (int, float),
                    "checkpoint_cost": (int, float),
                    "max_lost_time": (int, float),
                    "mtbf": (type(None), int, float),
                },
                "results": {
                    "checkpoint_interval": (int, float),
                    "checkpoints": int,
                    "overhead_fraction": (int, float),
                    "method": str,
                },
            },
        )

    def test_stencil_generator_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "differentiation-schemes"
                / "scripts"
                / "stencil_generator.py"
            ),
            "--order",
            "1",
            "--accuracy",
            "2",
            "--scheme",
            "central",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "order": int,
                    "accuracy": int,
                    "scheme": str,
                    "dx": (int, float),
                    "offsets": (type(None), list),
                },
                "results": {
                    "offsets": [int],
                    "coefficients": [float],
                    "order": int,
                    "accuracy": int,
                    "scheme": str,
                },
            },
        )

    def test_scheme_selector_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "differentiation-schemes"
                / "scripts"
                / "scheme_selector.py"
            ),
            "--smooth",
            "--periodic",
            "--order",
            "1",
            "--accuracy",
            "4",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "smooth": bool,
                    "discontinuous": bool,
                    "periodic": bool,
                    "boundary": bool,
                    "order": int,
                    "accuracy": int,
                },
                "results": {
                    "recommended": [str],
                    "alternatives": [str],
                    "notes": [str],
                },
            },
        )

    def test_truncation_error_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "differentiation-schemes"
                / "scripts"
                / "truncation_error.py"
            ),
            "--dx",
            "0.1",
            "--accuracy",
            "2",
            "--scale",
            "1.0",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "dx": (int, float),
                    "accuracy": int,
                    "scale": (int, float),
                },
                "results": {
                    "error_scale": (int, float),
                    "order": int,
                    "reduction_if_halved": int,
                },
            },
        )

    def test_grid_sizing_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "mesh-generation"
                / "scripts"
                / "grid_sizing.py"
            ),
            "--length",
            "1",
            "--resolution",
            "10",
            "--dims",
            "2",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "length": (int, float),
                    "resolution": int,
                    "dims": int,
                    "dx": (type(None), int, float),
                },
                "results": {
                    "dx": (int, float),
                    "counts": [int],
                    "notes": [str],
                },
            },
        )

    def test_mesh_quality_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "mesh-generation"
                / "scripts"
                / "mesh_quality.py"
            ),
            "--dx",
            "1",
            "--dy",
            "1",
            "--dz",
            "2",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "dx": (int, float),
                    "dy": (int, float),
                    "dz": (int, float),
                },
                "results": {
                    "aspect_ratio": (int, float),
                    "skewness": (int, float),
                    "quality_flags": [str],
                },
            },
        )

    def test_preflight_checker_schema(self):
        config_path = ROOT / "tests" / "integration" / "sim_config.json"
        config_path.write_text('{"dt": 1e-4, "dx": 1e-6, "output_dir": "out"}\n')
        try:
            cmd = [
                str(
                    ROOT
                    / "skills"
                    / "simulation-workflow"
                    / "simulation-validator"
                    / "scripts"
                    / "preflight_checker.py"
                ),
                "--config",
                str(config_path),
                "--required",
                "dt,dx",
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {
                        "config": str,
                        "required": [str],
                        "ranges": (type(None), str),
                        "output_dir": (type(None), str),
                        "min_free_gb": (int, float),
                    },
                    "report": {
                        "status": str,
                        "blockers": [str],
                        "warnings": [str],
                    },
                },
            )
        finally:
            config_path.unlink(missing_ok=True)

    def test_runtime_monitor_schema(self):
        log_path = ROOT / "tests" / "integration" / "sim.log"
        log_path.write_text("residual=1e-2 dt=1e-4\nresidual=5e-3 dt=1e-4\n")
        try:
            cmd = [
                str(
                    ROOT
                    / "skills"
                    / "simulation-workflow"
                    / "simulation-validator"
                    / "scripts"
                    / "runtime_monitor.py"
                ),
                "--log",
                str(log_path),
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {
                        "log": str,
                        "residual_pattern": str,
                        "dt_pattern": str,
                        "residual_growth": (int, float),
                        "dt_drop": (int, float),
                    },
                    "results": {
                        "alerts": [str],
                        "residual_stats": dict,
                        "dt_stats": dict,
                    },
                },
            )
        finally:
            log_path.unlink(missing_ok=True)

    def test_result_validator_schema(self):
        metrics_path = ROOT / "tests" / "integration" / "metrics.json"
        metrics_path.write_text(
            '{"mass_initial": 1.0, "mass_final": 1.0001, "energy_history": [1.0, 0.9], "field_min": 0.0, "field_max": 1.0}'
        )
        try:
            cmd = [
                str(
                    ROOT
                    / "skills"
                    / "simulation-workflow"
                    / "simulation-validator"
                    / "scripts"
                    / "result_validator.py"
                ),
                "--metrics",
                str(metrics_path),
                "--bound-min",
                "0",
                "--bound-max",
                "1",
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {
                        "metrics": str,
                        "bound_min": (type(None), int, float),
                        "bound_max": (type(None), int, float),
                        "mass_tol": (int, float),
                    },
                    "results": {
                        "checks": dict,
                        "failed_checks": [str],
                        "confidence_score": (int, float),
                    },
                },
            )
        finally:
            metrics_path.unlink(missing_ok=True)

    def test_failure_diagnoser_schema(self):
        log_path = ROOT / "tests" / "integration" / "failure.log"
        log_path.write_text("nan encountered")
        try:
            cmd = [
                str(
                    ROOT
                    / "skills"
                    / "simulation-workflow"
                    / "simulation-validator"
                    / "scripts"
                    / "failure_diagnoser.py"
                ),
                "--log",
                str(log_path),
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {"log": str},
                    "results": {
                        "probable_causes": [str],
                        "recommended_fixes": [str],
                    },
                },
            )
        finally:
            log_path.unlink(missing_ok=True)

    def test_doe_generator_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "simulation-workflow"
                / "parameter-optimization"
                / "scripts"
                / "doe_generator.py"
            ),
            "--params",
            "3",
            "--budget",
            "10",
            "--method",
            "lhs",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "params": int,
                    "budget": int,
                    "method": str,
                    "seed": int,
                },
                "results": {
                    "method": str,
                    "samples": list,
                    "coverage": dict,
                },
            },
        )

    def test_optimizer_selector_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "simulation-workflow"
                / "parameter-optimization"
                / "scripts"
                / "optimizer_selector.py"
            ),
            "--dim",
            "3",
            "--budget",
            "40",
            "--noise",
            "low",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "dim": int,
                    "budget": int,
                    "noise": str,
                    "constraints": bool,
                },
                "results": {
                    "recommended": [str],
                    "expected_evals": int,
                    "notes": [str],
                },
            },
        )

    def test_sensitivity_summary_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "simulation-workflow"
                / "parameter-optimization"
                / "scripts"
                / "sensitivity_summary.py"
            ),
            "--scores",
            "0.2,0.5,0.3",
            "--names",
            "a,b,c",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "scores": [float],
                    "names": [str],
                },
                "results": {
                    "ranking": list,
                    "notes": [str],
                },
            },
        )

    def test_surrogate_builder_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "simulation-workflow"
                / "parameter-optimization"
                / "scripts"
                / "surrogate_builder.py"
            ),
            "--x",
            "0,1,2",
            "--y",
            "1,2,3",
            "--model",
            "rbf",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "x": [float],
                    "y": [float],
                    "model": str,
                },
                "results": {
                    "model_type": str,
                    "metrics": dict,
                    "notes": [str],
                },
            },
        )

    def test_linear_solver_selector_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "linear-solvers"
                / "scripts"
                / "solver_selector.py"
            ),
            "--symmetric",
            "--positive-definite",
            "--sparse",
            "--size",
            "100000",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "symmetric": bool,
                    "positive_definite": bool,
                    "sparse": bool,
                    "size": int,
                    "nearly_symmetric": bool,
                    "ill_conditioned": bool,
                    "complex_valued": bool,
                    "memory_limited": bool,
                },
                "results": {
                    "recommended": [str],
                    "alternatives": [str],
                    "notes": [str],
                },
            },
        )

    def test_convergence_diagnostics_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "linear-solvers"
                / "scripts"
                / "convergence_diagnostics.py"
            ),
            "--residuals",
            "1,0.2,0.05,0.01",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {"residuals": [float]},
                "results": {
                    "rate": (int, float),
                    "stagnation": bool,
                    "recommended_action": str,
                },
            },
        )

    def test_sparsity_stats_schema(self):
        matrix_path = ROOT / "tests" / "integration" / "sparsity_matrix.txt"
        matrix_path.write_text("1 0 0\n0 0 0\n0 0 2\n")
        try:
            cmd = [
                str(
                    ROOT
                    / "skills"
                    / "core-numerical"
                    / "linear-solvers"
                    / "scripts"
                    / "sparsity_stats.py"
                ),
                "--matrix",
                str(matrix_path),
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {
                        "matrix": str,
                        "symmetry_tol": (int, float),
                    },
                    "results": {
                        "shape": [int],
                        "nnz": int,
                        "density": (int, float),
                        "bandwidth": int,
                        "symmetry": bool,
                    },
                },
            )
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_preconditioner_advisor_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "linear-solvers"
                / "scripts"
                / "preconditioner_advisor.py"
            ),
            "--matrix-type",
            "spd",
            "--sparse",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "matrix_type": str,
                    "sparse": bool,
                    "ill_conditioned": bool,
                    "saddle_point": bool,
                    "symmetric": bool,
                },
                "results": {
                    "suggested": [str],
                    "notes": [str],
                },
            },
        )

    def test_scaling_equilibration_schema(self):
        matrix_path = ROOT / "tests" / "integration" / "scale_matrix.txt"
        matrix_path.write_text("2 0\n0 4\n")
        try:
            cmd = [
                str(
                    ROOT
                    / "skills"
                    / "core-numerical"
                    / "linear-solvers"
                    / "scripts"
                    / "scaling_equilibration.py"
                ),
                "--matrix",
                str(matrix_path),
                "--symmetric",
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {
                        "matrix": str,
                        "symmetry_tol": (int, float),
                        "symmetric": bool,
                    },
                    "results": {
                        "shape": [int],
                        "row_scale": [float],
                        "col_scale": [float],
                        "row_scale_min": (int, float),
                        "row_scale_max": (int, float),
                        "col_scale_min": (int, float),
                        "col_scale_max": (int, float),
                        "zero_rows": [int],
                        "zero_cols": [int],
                        "symmetric_scale": (type(None), list),
                        "symmetric": bool,
                        "notes": [str],
                    },
                },
            )
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_residual_norms_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "linear-solvers"
                / "scripts"
                / "residual_norms.py"
            ),
            "--residual",
            "1,0.1,0.01",
            "--rhs",
            "1,0,0",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "residual": [float],
                    "rhs": (type(None), list),
                    "initial": (type(None), list),
                    "abs_tol": (int, float),
                    "rel_tol": (int, float),
                    "norm": str,
                    "require_both": bool,
                },
                "results": {
                    "residual_norms": dict,
                    "reference_norms": (type(None), dict),
                    "relative_norms": (type(None), dict),
                    "meta": dict,
                },
            },
        )

    # Nonlinear solver tests

    def test_nonlinear_solver_selector_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "nonlinear-solvers"
                / "scripts"
                / "solver_selector.py"
            ),
            "--jacobian-available",
            "--size",
            "1000",
            "--smooth",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "jacobian_available": bool,
                    "jacobian_expensive": bool,
                    "problem_size": int,
                    "spd_hessian": bool,
                    "smooth_objective": bool,
                    "constraint_type": str,
                    "memory_limited": bool,
                    "high_accuracy": bool,
                },
                "results": {
                    "recommended": [str],
                    "alternatives": [str],
                    "notes": [str],
                },
            },
        )

    def test_nonlinear_convergence_analyzer_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "nonlinear-solvers"
                / "scripts"
                / "convergence_analyzer.py"
            ),
            "--residuals",
            "1,0.1,0.01,0.001",
            "--tolerance",
            "1e-6",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "residuals": [float],
                    "tolerance": (int, float),
                },
                "results": {
                    "converged": bool,
                    "iterations": int,
                    "final_residual": (int, float),
                    "convergence_type": str,
                    "estimated_rate": (type(None), int, float),
                    "diagnosis": str,
                    "recommended_action": str,
                },
            },
        )

    def test_nonlinear_jacobian_diagnostics_schema(self):
        matrix_path = ROOT / "tests" / "integration" / "jacobian_matrix.txt"
        matrix_path.write_text("2 1\n1 3\n")
        try:
            cmd = [
                str(
                    ROOT
                    / "skills"
                    / "core-numerical"
                    / "nonlinear-solvers"
                    / "scripts"
                    / "jacobian_diagnostics.py"
                ),
                "--matrix",
                str(matrix_path),
                "--json",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            assert_schema(
                payload,
                {
                    "inputs": {
                        "matrix": str,
                        "finite_diff_matrix": (type(None), str),
                        "tolerance": (int, float),
                    },
                    "results": {
                        "shape": [int],
                        "condition_number": (int, float),
                        "rank_deficient": bool,
                        "estimated_rank": int,
                        "singular_value_min": (int, float),
                        "singular_value_max": (int, float),
                        "jacobian_quality": str,
                        "finite_diff_error": (type(None), int, float),
                        "notes": [str],
                    },
                },
            )
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_nonlinear_globalization_advisor_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "nonlinear-solvers"
                / "scripts"
                / "globalization_advisor.py"
            ),
            "--problem-type",
            "optimization",
            "--jacobian-quality",
            "good",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "problem_type": str,
                    "jacobian_quality": str,
                    "previous_failures": int,
                    "oscillating_residual": bool,
                    "step_rejection_rate": (int, float),
                },
                "results": {
                    "strategy": str,
                    "line_search_type": (type(None), str),
                    "trust_region_type": (type(None), str),
                    "initial_damping": (int, float),
                    "parameters": dict,
                    "notes": [str],
                },
            },
        )

    def test_nonlinear_residual_monitor_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "nonlinear-solvers"
                / "scripts"
                / "residual_monitor.py"
            ),
            "--residuals",
            "1,0.5,0.25,0.125",
            "--target-tolerance",
            "1e-8",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "residuals": [float],
                    "function_evals": (type(None), list),
                    "step_sizes": (type(None), list),
                    "target_tolerance": (int, float),
                },
                "results": {
                    "residual_reduction": (int, float),
                    "iterations": int,
                    "converged": bool,
                    "patterns_detected": [str],
                    "alerts": [str],
                    "recommendations": [str],
                },
            },
        )

    def test_nonlinear_step_quality_schema(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "nonlinear-solvers"
                / "scripts"
                / "step_quality.py"
            ),
            "--predicted-reduction",
            "1.0",
            "--actual-reduction",
            "0.8",
            "--step-norm",
            "0.5",
            "--gradient-norm",
            "1.0",
            "--trust-radius",
            "1.0",
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        assert_schema(
            payload,
            {
                "inputs": {
                    "predicted_reduction": (int, float),
                    "actual_reduction": (int, float),
                    "step_norm": (int, float),
                    "gradient_norm": (int, float),
                    "trust_radius": (type(None), int, float),
                },
                "results": {
                    "ratio": (type(None), int, float),
                    "step_quality": str,
                    "accept_step": bool,
                    "trust_radius_action": (type(None), str),
                    "suggested_trust_radius": (type(None), int, float),
                    "notes": [str],
                },
            },
        )


if __name__ == "__main__":
    unittest.main()
