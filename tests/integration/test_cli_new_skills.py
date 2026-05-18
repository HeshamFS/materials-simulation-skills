import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


class TestNewSkillCliTools(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def assert_json_ok(self, args):
        result = self.run_cmd(args)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("inputs", payload)
        self.assertIn("results", payload)
        return payload

    def test_benchmark_mms_planner_cli(self):
        payload = self.assert_json_ok(
            [
                "skills/verification-validation/benchmark-and-mms-planner/scripts/benchmark_mms_planner.py",
                "--model",
                "diffusion",
                "--quantity",
                "L2 error",
                "--dimension",
                "2",
                "--expected-order",
                "2",
                "--reference",
                "analytic",
                "--json",
            ]
        )
        self.assertIn("refinement_protocol", payload["results"])

    def test_workflow_engine_mapper_cli(self):
        payload = self.assert_json_ok(
            [
                "skills/simulation-workflow/workflow-engine-mapper/scripts/workflow_engine_mapper.py",
                "--task",
                "VASP relax static DOS for 50 structures",
                "--code",
                "vasp",
                "--runs",
                "50",
                "--needs-restart",
                "--json",
            ]
        )
        self.assertIn(payload["results"]["recommended_engine"], {"atomate2", "jobflow", "aiida", "pyiron"})

    def test_fair_packager_cli(self):
        fixture = ROOT / "tests" / "fixtures" / "fair_input.txt"
        fixture.write_text("demo\n", encoding="utf-8")
        try:
            payload = self.assert_json_ok(
                [
                    "skills/data-management/fair-simulation-packager/scripts/fair_packager.py",
                    "--project-name",
                    "demo",
                    "--engine",
                    "LAMMPS",
                    "--inputs",
                    str(fixture),
                    "--units",
                    "energy=eV",
                    "--json",
                ]
            )
        finally:
            fixture.unlink(missing_ok=True)
        manifest = payload["results"]["manifest"]
        self.assertTrue(manifest["fair_checks"]["has_hashes_for_existing_files"])

    def test_md_analysis_planner_cli(self):
        payload = self.assert_json_ok(
            [
                "skills/simulation-workflow/md-analysis-planner/scripts/md_analysis_planner.py",
                "--system",
                "oxide glass",
                "--goals",
                "rdf,coordination,bond-angle",
                "--trajectory-format",
                "dump",
                "--json",
            ]
        )
        self.assertGreaterEqual(len(payload["results"]["analysis_plan"]), 3)

    def test_hpc_runtime_doctor_cli(self):
        payload = self.assert_json_ok(
            [
                "skills/hpc-deployment/hpc-runtime-doctor/scripts/hpc_runtime_doctor.py",
                "--scheduler",
                "slurm",
                "--nodes",
                "2",
                "--tasks",
                "128",
                "--cpus-per-task",
                "1",
                "--symptoms",
                "slow-gpu",
                "--uses-openmp",
                "--uses-gpu",
                "--gpus",
                "4",
                "--json",
            ]
        )
        self.assertIn("warnings", payload["results"])

    def test_failure_triage_cli(self):
        payload = self.assert_json_ok(
            [
                "skills/robustness/simulation-failure-triage/scripts/failure_triage.py",
                "--code",
                "LAMMPS",
                "--stage",
                "runtime",
                "--symptoms",
                "nan",
                "--log-text",
                "Lost atoms and NaN temperature",
                "--json",
            ]
        )
        self.assertIn("pressure-blowup", payload["results"]["evidence"]["symptoms"])

    def test_invalid_cli_returns_exit_2(self):
        result = self.run_cmd(
            [
                "skills/hpc-deployment/hpc-runtime-doctor/scripts/hpc_runtime_doctor.py",
                "--nodes",
                "0",
            ]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("nodes", result.stderr)


if __name__ == "__main__":
    unittest.main()
