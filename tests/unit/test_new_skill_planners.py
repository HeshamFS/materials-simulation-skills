import json
import tempfile
import unittest
from pathlib import Path

from tests.unit._utils import load_module


benchmark = load_module(
    "benchmark_mms_planner",
    "skills/verification-validation/benchmark-and-mms-planner/scripts/benchmark_mms_planner.py",
)
workflow = load_module(
    "workflow_engine_mapper",
    "skills/simulation-workflow/workflow-engine-mapper/scripts/workflow_engine_mapper.py",
)
fair = load_module(
    "fair_packager",
    "skills/data-management/fair-simulation-packager/scripts/fair_packager.py",
)
md = load_module(
    "md_analysis_planner",
    "skills/simulation-workflow/md-analysis-planner/scripts/md_analysis_planner.py",
)
hpc = load_module(
    "hpc_runtime_doctor",
    "skills/hpc-deployment/hpc-runtime-doctor/scripts/hpc_runtime_doctor.py",
)
triage = load_module(
    "failure_triage",
    "skills/robustness/simulation-failure-triage/scripts/failure_triage.py",
)


class TestBenchmarkMmsPlanner(unittest.TestCase):
    def test_diffusion_mms_high_risk(self):
        result = benchmark.plan_vv(
            model="diffusion",
            quantity="L2 temperature error",
            dimension=2,
            expected_order=2.0,
            reference="analytic",
            risk="high",
        )
        self.assertIn("MMS", result["verification_strategy"])
        self.assertEqual(result["refinement_protocol"]["levels"], 4)
        self.assertLess(result["refinement_protocol"]["accept_observed_order_min"], 2.0)

    def test_invalid_dimension(self):
        with self.assertRaisesRegex(ValueError, "dimension"):
            benchmark.plan_vv("diffusion", "error", 4, 2.0, "analytic", "medium")


class TestWorkflowEngineMapper(unittest.TestCase):
    def test_aiida_for_hpc_provenance_campaign(self):
        result = workflow.recommend_engine(
            task="QE screening campaign",
            code="qe",
            runs=200,
            needs_provenance=True,
            needs_restart=True,
            hpc=True,
            preferred="auto",
        )
        self.assertEqual(result["recommended_engine"], "aiida")
        self.assertTrue(result["restart_strategy"]["needed"])
        self.assertIn("metadata/workflow.json", result["storage_layout"])

    def test_one_off_for_small_local_task(self):
        result = workflow.recommend_engine(
            task="inspect one ASE structure",
            code="ase",
            runs=1,
            needs_provenance=False,
            needs_restart=False,
            hpc=False,
            preferred="auto",
        )
        self.assertEqual(result["recommended_engine"], "one-off")


class TestFairPackager(unittest.TestCase):
    def test_manifest_hashes_existing_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_file = root / "in.lmp"
            output_file = root / "log.lammps"
            input_file.write_text("units metal\n", encoding="utf-8")
            output_file.write_text("done\n", encoding="utf-8")
            result = fair.build_manifest(
                project_name="demo",
                engine="LAMMPS",
                inputs=[str(input_file)],
                outputs=[str(output_file)],
                units={"energy": "eV"},
                structure_id="local:demo",
                engine_version="2026",
            )
        self.assertTrue(result["fair_checks"]["has_hashes_for_existing_files"])
        self.assertEqual(result["missing_files"], [])
        self.assertEqual(result["units"]["energy"], "eV")

    def test_units_validation(self):
        with self.assertRaisesRegex(ValueError, "key=value"):
            fair.parse_units("energy")


class TestMdAnalysisPlanner(unittest.TestCase):
    def test_diffusion_requires_unwrapped_positions(self):
        result = md.plan_md_analysis(
            system="solid electrolyte",
            goals=["diffusion"],
            trajectory_format="dump",
            has_velocities=False,
            has_stress=False,
            unwrap_needed=True,
            timestep_fs=5.0,
        )
        self.assertIn("unwrapped positions", result["required_data"])
        self.assertTrue(any("unwrapped" in warning for warning in result["warnings"]))

    def test_vacf_blocked_without_velocities(self):
        result = md.plan_md_analysis("water", ["vacf"], "xyz", False, False, False, 1.0)
        self.assertEqual(result["analysis_plan"][0]["status"], "blocked")


class TestHpcRuntimeDoctor(unittest.TestCase):
    def test_openmp_layout_warning(self):
        result = hpc.diagnose_hpc(
            scheduler="slurm",
            nodes=2,
            tasks=128,
            cpus_per_task=1,
            gpus=4,
            symptoms=["slow-gpu"],
            uses_mpi=True,
            uses_openmp=True,
            uses_gpu=True,
            walltime="02:00:00",
            scratch=False,
        )
        self.assertTrue(any("OpenMP" in warning for warning in result["warnings"]))
        self.assertEqual(result["resource_layout"]["tasks_per_node"], 64)

    def test_invalid_nodes(self):
        with self.assertRaisesRegex(ValueError, "nodes"):
            hpc.diagnose_hpc("slurm", 0, 1, 1, 0, [], False, False, False, None, False)


class TestFailureTriage(unittest.TestCase):
    def test_infers_lost_atoms_from_log(self):
        result = triage.triage_failure(
            code="LAMMPS",
            stage="runtime",
            symptoms=["nan"],
            log_text="ERROR: Lost atoms: original 100 current 98",
            recent_change="larger timestep",
        )
        symptoms = result["evidence"]["symptoms"]
        self.assertIn("pressure-blowup", symptoms)
        self.assertTrue(any("recent change" in action for action in result["immediate_actions"]))

    def test_invalid_stage(self):
        with self.assertRaisesRegex(ValueError, "stage"):
            triage.triage_failure("VASP", "bad", [], "", None)


if __name__ == "__main__":
    unittest.main()
