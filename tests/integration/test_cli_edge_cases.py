import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "skills" / "core-numerical" / "numerical-stability" / "scripts"


class TestCliEdgeCases(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_von_neumann_invalid_nk(self):
        cmd = [
            str(SCRIPTS / "von_neumann_analyzer.py"),
            "--coeffs",
            "0.5,0.5",
            "--nk",
            "1",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("nk must be > 1", result.stderr)

    def test_matrix_condition_non_finite(self):
        matrix_path = ROOT / "tests" / "integration" / "nan_matrix.txt"
        matrix_path.write_text("1 0\n0 nan\n")
        try:
            cmd = [
                str(SCRIPTS / "matrix_condition.py"),
                "--matrix",
                str(matrix_path),
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("non-finite", result.stderr.lower())
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_stiffness_detector_empty_eigs(self):
        cmd = [
            str(SCRIPTS / "stiffness_detector.py"),
            "--eigs=",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("eigs must be a comma-separated list", result.stderr)

    def test_cfl_invalid_dimensions(self):
        cmd = [
            str(SCRIPTS / "cfl_checker.py"),
            "--dx",
            "0.1",
            "--dt",
            "0.01",
            "--velocity",
            "1.0",
            "--dimensions",
            "0",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dimensions must be positive", result.stderr)

    def test_von_neumann_kmin_kmax(self):
        cmd = [
            str(SCRIPTS / "von_neumann_analyzer.py"),
            "--coeffs",
            "0.2,0.6,0.2",
            "--kmin",
            "1.0",
            "--kmax",
            "0.0",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("kmin must be < kmax", result.stderr)

    def test_matrix_condition_non_square(self):
        matrix_path = ROOT / "tests" / "integration" / "rect_matrix.txt"
        matrix_path.write_text("1 0 0\n0 1 0\n")
        try:
            cmd = [
                str(SCRIPTS / "matrix_condition.py"),
                "--matrix",
                str(matrix_path),
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("matrix must be square", result.stderr.lower())
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_matrix_condition_invalid_norm(self):
        matrix_path = ROOT / "tests" / "integration" / "square_matrix.txt"
        matrix_path.write_text("1 0\n0 2\n")
        try:
            cmd = [
                str(SCRIPTS / "matrix_condition.py"),
                "--matrix",
                str(matrix_path),
                "--norm",
                "bad",
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("norm must be one of", result.stderr.lower())
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_error_norm_missing_scale(self):
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
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("solution or scale must be provided", result.stderr)

    def test_adaptive_step_negative_dt(self):
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
            "-0.1",
            "--error-norm",
            "0.5",
            "--order",
            "2",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dt must be positive", result.stderr)

    def test_integrator_selector_invalid_dimension(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "numerical-integration"
                / "scripts"
                / "integrator_selector.py"
            ),
            "--dimension",
            "0",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dimension must be positive", result.stderr)

    def test_imex_split_missing_terms(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "numerical-integration"
                / "scripts"
                / "imex_split_planner.py"
            ),
            "--json",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Provide at least one", result.stderr)

    def test_splitting_error_invalid_dt(self):
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
            "0",
            "--commutator-norm",
            "1",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dt must be positive", result.stderr)

    def test_timestep_planner_invalid_dt(self):
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
            "-1",
            "--dt-limit",
            "1e-3",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dt_target", result.stderr)

    def test_output_schedule_invalid_interval(self):
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
            "0",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("interval must be positive", result.stderr)

    def test_checkpoint_planner_invalid_runtime(self):
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
            "0",
            "--checkpoint-cost",
            "10",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("run_time", result.stderr)

    def test_stencil_generator_invalid_order(self):
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
            "0",
            "--accuracy",
            "2",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("order must be positive", result.stderr)

    def test_scheme_selector_invalid_flags(self):
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
            "--discontinuous",
            "--order",
            "1",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("smooth and discontinuous", result.stderr)

    def test_truncation_error_invalid_dx(self):
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
            "0",
            "--accuracy",
            "2",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dx must be positive", result.stderr)

    def test_grid_sizing_invalid_length(self):
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
            "0",
            "--resolution",
            "10",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("length must be positive", result.stderr)

    def test_mesh_quality_invalid(self):
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
            "0",
            "--dy",
            "1",
            "--dz",
            "1",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dx, dy, dz must be positive", result.stderr)

    def test_preflight_invalid_config(self):
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
            "missing.json",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Config not found", result.stderr)

    def test_runtime_monitor_invalid_log(self):
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
            "missing.log",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)

    def test_result_validator_invalid_metrics(self):
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
            "missing.json",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)

    def test_failure_diagnoser_invalid_log(self):
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
            "missing.log",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)

    def test_doe_generator_invalid_budget(self):
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
            "2",
            "--budget",
            "0",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("budget must be positive", result.stderr)

    def test_optimizer_selector_invalid_dim(self):
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
            "0",
            "--budget",
            "10",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dim must be positive", result.stderr)

    def test_sensitivity_summary_invalid_names(self):
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
            "0.1,0.2",
            "--names",
            "a,b,c",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("names count", result.stderr)

    def test_surrogate_builder_invalid_model(self):
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
            "0,1",
            "--y",
            "1,2",
            "--model",
            "bad",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--model", result.stderr)

    def test_linear_solver_invalid_size(self):
        cmd = [
            str(
                ROOT
                / "skills"
                / "core-numerical"
                / "linear-solvers"
                / "scripts"
                / "solver_selector.py"
            ),
            "--size",
            "0",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("size must be positive", result.stderr)

    def test_convergence_invalid_residuals(self):
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
            "1",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at least 2", result.stderr)

    def test_preconditioner_invalid_type(self):
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
            "bad",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--matrix-type", result.stderr)

    def test_scaling_equilibration_non_square(self):
        matrix_path = ROOT / "tests" / "integration" / "rect_scale.txt"
        matrix_path.write_text("1 0 0\n0 1 0\n")
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
            ]
            result = self.run_cmd(cmd)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("square matrix", result.stderr)
        finally:
            matrix_path.unlink(missing_ok=True)

    def test_residual_norms_negative_tol(self):
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
            "1,0.1",
            "--abs-tol=-1e-3",
        ]
        result = self.run_cmd(cmd)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("abs_tol", result.stderr)


if __name__ == "__main__":
    unittest.main()
