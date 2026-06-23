import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def test_unknown_transient_model_matches_general(self):
        # Regression (F2): an unlisted transient PDE must fall back to 'general' for BOTH
        # benchmark selection AND the time-refinement decision -- it must not be told to
        # skip time refinement just because its name is missing from the table.
        unknown = benchmark.plan_vv(
            model="magnetohydrodynamics",
            quantity="x",
            dimension=2,
            expected_order=2.0,
            reference="benchmark",
            risk="medium",
        )
        general = benchmark.plan_vv(
            model="general",
            quantity="x",
            dimension=2,
            expected_order=2.0,
            reference="benchmark",
            risk="medium",
        )
        self.assertEqual(unknown["effective_model"], "general")
        self.assertTrue(unknown["refinement_protocol"]["include_time_refinement"])
        self.assertEqual(
            unknown["refinement_protocol"]["include_time_refinement"],
            general["refinement_protocol"]["include_time_refinement"],
        )
        self.assertEqual(unknown["benchmark_cases"], general["benchmark_cases"])

    def test_known_model_reports_itself_as_effective(self):
        result = benchmark.plan_vv("elasticity", "x", 2, 2.0, "benchmark", "low")
        self.assertEqual(result["effective_model"], "elasticity")
        # Static elasticity is not transient -> no time refinement.
        self.assertFalse(result["refinement_protocol"]["include_time_refinement"])

    def test_acceptance_band_is_relative_to_order(self):
        # Regression (F3): the band must be a relative fraction of the formal order, not a
        # fixed absolute offset, and consistent across orders.
        high2 = benchmark.plan_vv("diffusion", "x", 2, 2.0, "analytic", "high")
        high5 = benchmark.plan_vv("diffusion", "x", 2, 5.0, "analytic", "high")
        self.assertAlmostEqual(
            high2["refinement_protocol"]["accept_observed_order_min"], 1.8, places=3
        )
        self.assertAlmostEqual(
            high5["refinement_protocol"]["accept_observed_order_min"], 4.5, places=3
        )
        med2 = benchmark.plan_vv("diffusion", "x", 2, 2.0, "analytic", "medium")
        self.assertAlmostEqual(
            med2["refinement_protocol"]["accept_observed_order_min"], 1.6, places=3
        )

    def test_acceptance_band_floored_at_first_order(self):
        # Regression (F3): the threshold must never drop below first-order convergence.
        result = benchmark.plan_vv("diffusion", "x", 2, 1.0, "analytic", "medium")
        self.assertEqual(
            result["refinement_protocol"]["accept_observed_order_min"], 1.0
        )
        # And the high-risk diffusion case from eval 1 still leaves headroom below 2.0.
        eval1 = benchmark.plan_vv("diffusion", "x", 2, 2.0, "analytic", "high")
        self.assertLess(
            eval1["refinement_protocol"]["accept_observed_order_min"], 2.0
        )

    def test_string_input_caps(self):
        # Regression for the SKILL.md "## Security" 256-character caps.
        with self.assertRaisesRegex(ValueError, "model must be at most"):
            benchmark.plan_vv("a" * 300, "x", 2, 2.0, "analytic", "medium")
        with self.assertRaisesRegex(ValueError, "quantity must be at most"):
            benchmark.plan_vv("diffusion", "q" * 300, 2, 2.0, "analytic", "medium")


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

    def test_one_off_emits_migration_trigger(self):
        # Regression (F2): one-off must emit a concrete forward-looking trigger.
        result = workflow.recommend_engine(
            task="one local ASE test calculation to inspect a structure",
            code="ase",
            runs=1,
            needs_provenance=False,
            needs_restart=False,
            hpc=False,
            preferred="auto",
        )
        self.assertEqual(result["recommended_engine"], "one-off")
        self.assertTrue(result["migration_triggers"])
        self.assertTrue(
            any("migrate to a workflow engine" in t for t in result["migration_triggers"])
        )

    def test_branch_and_sweep_dag_is_composed(self):
        # Regression (F4): branch+sweep must not overwrite each other.
        result = workflow.recommend_engine(
            task="relax static dos screening campaign over 200 oxides",
            code="vasp",
            runs=200,
            needs_provenance=False,
            needs_restart=False,
            hpc=False,
            preferred="auto",
        )
        dag = result["dag_pattern"]
        self.assertIn("map over structures", dag)
        self.assertIn("relax -> static -> property branches", dag)
        self.assertIn("collect -> rank", dag)

    def test_branch_only_dag(self):
        result = workflow.recommend_engine(
            task="vasp relax static dos calculations across 50 structures",
            code="vasp",
            runs=50,
            needs_provenance=False,
            needs_restart=False,
            hpc=False,
            preferred="auto",
        )
        self.assertEqual(result["dag_pattern"], "relax -> static -> property branches")

    def test_sweep_only_dag(self):
        result = workflow.recommend_engine(
            task="screen 200 candidate structures",
            code="vasp",
            runs=200,
            needs_provenance=False,
            needs_restart=False,
            hpc=False,
            preferred="auto",
        )
        self.assertEqual(
            result["dag_pattern"], "map over structures/parameters -> collect -> rank"
        )

    def test_runs_must_be_positive_int(self):
        for bad in (0, -3, True):
            with self.assertRaises(ValueError):
                workflow.recommend_engine(
                    task="x",
                    code="vasp",
                    runs=bad,
                    needs_provenance=False,
                    needs_restart=False,
                    hpc=False,
                    preferred="auto",
                )

    def test_runs_capped(self):
        with self.assertRaises(ValueError):
            workflow.recommend_engine(
                task="x",
                code="vasp",
                runs=10_000_000,
                needs_provenance=False,
                needs_restart=False,
                hpc=False,
                preferred="auto",
            )

    def test_overlong_task_rejected(self):
        with self.assertRaises(ValueError):
            workflow.recommend_engine(
                task="a" * 2001,
                code="vasp",
                runs=1,
                needs_provenance=False,
                needs_restart=False,
                hpc=False,
                preferred="auto",
            )

    def test_overlong_code_rejected(self):
        with self.assertRaises(ValueError):
            workflow.recommend_engine(
                task="x",
                code="v" * 101,
                runs=1,
                needs_provenance=False,
                needs_restart=False,
                hpc=False,
                preferred="auto",
            )

    def test_invalid_preferred_rejected(self):
        with self.assertRaises(ValueError):
            workflow.recommend_engine(
                task="x",
                code="vasp",
                runs=1,
                needs_provenance=False,
                needs_restart=False,
                hpc=False,
                preferred="not-an-engine",
            )


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

    def test_blocked_not_demoted_by_missing_timestep(self):
        # Regression for F1: a VDOS goal with no velocities AND no timestep must
        # stay "blocked" (the fundamental blocker), not be downgraded to the
        # recoverable "needs time axis".
        result = md.plan_md_analysis(
            system="crystal",
            goals=["vdos"],
            trajectory_format="dump",
            has_velocities=False,
            has_stress=False,
            unwrap_needed=False,
            timestep_fs=None,
        )
        self.assertEqual(result["analysis_plan"][0]["status"], "blocked")
        # Both warnings must still be emitted so the user learns about both gaps.
        self.assertTrue(any("velocit" in w for w in result["warnings"]))
        self.assertTrue(any("timestep" in w for w in result["warnings"]))

    def test_needs_time_axis_when_only_timestep_missing(self):
        # A goal that is otherwise ready but lacks a timestep reports the
        # recoverable status, confirming the escalation ordering is correct.
        result = md.plan_md_analysis(
            system="crystal",
            goals=["vdos"],
            trajectory_format="dump",
            has_velocities=True,
            has_stress=False,
            unwrap_needed=False,
            timestep_fs=None,
        )
        self.assertEqual(result["analysis_plan"][0]["status"], "needs time axis")

    def test_diffusion_emits_regime_and_finite_size_warnings(self):
        # Regression for F4: structured output must surface diffusive-regime and
        # finite-size (Yeh-Hummer) guidance.
        result = md.plan_md_analysis(
            system="solid electrolyte",
            goals=["diffusion"],
            trajectory_format="dump",
            has_velocities=False,
            has_stress=False,
            unwrap_needed=True,
            timestep_fs=5.0,
        )
        self.assertTrue(any("diffusive regime" in w for w in result["warnings"]))
        self.assertTrue(any("Yeh-Hummer" in w for w in result["warnings"]))
        # Unwrapping requires cell + image flags.
        self.assertIn("cell", result["required_data"])
        self.assertIn("image flags", result["required_data"])

    def test_input_caps_reject_oversized_inputs(self):
        # Regression for the SKILL.md "## Security" caps.
        with self.assertRaisesRegex(ValueError, "system must be at most"):
            md.plan_md_analysis("x" * 300, ["rdf"], "dump", False, False, False, None)
        with self.assertRaisesRegex(ValueError, "at most .* goals"):
            md.plan_md_analysis("water", ["rdf"] * 100, "dump", False, False, False, None)

    def test_cli_non_json_prints_warnings(self):
        # Regression for F2: the default human-readable main() output must
        # surface the safety-critical "Warnings:" section, not only plan lines.
        import io
        import contextlib

        argv = ["prog", "--system", "water", "--goals", "vacf", "--trajectory-format", "xyz"]
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "argv", argv):
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = md.main()
        self.assertEqual(rc, 0)
        stdout = out.getvalue()
        self.assertIn("Warnings:", stdout)
        self.assertIn("velocit", stdout)
        # Warnings are also mirrored to stderr so they survive stdout piping.
        self.assertIn("velocit", err.getvalue())

    def test_cli_invalid_input_exits_2(self):
        import io
        import contextlib

        argv = ["prog", "--system", "water", "--goals", "rdf", "--timestep-fs", "-1"]
        with mock.patch.object(sys, "argv", argv):
            with contextlib.redirect_stderr(io.StringIO()):
                rc = md.main()
        self.assertEqual(rc, 2)


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

    def test_ranks_per_gpu_multinode_fires(self):
        # F1 regression: 512 ranks / 4 GPUs = 128 ranks/GPU must warn on a multi-node
        # job. The old per-node-vs-total comparison missed this entirely.
        result = hpc.diagnose_hpc(
            scheduler="slurm",
            nodes=8,
            tasks=512,
            cpus_per_task=1,
            gpus=4,
            symptoms=[],
            uses_mpi=True,
            uses_openmp=False,
            uses_gpu=True,
            walltime=None,
            scratch=True,
        )
        self.assertTrue(any("ranks/GPU" in w for w in result["warnings"]))

    def test_gpus_per_node_resolves_total(self):
        # F1: --gpus-per-node overrides --gpus; total = gpus_per_node * nodes.
        # 64 ranks / (1*4)=4 GPUs = 16 ranks/GPU -> at the threshold, no warning.
        result = hpc.diagnose_hpc(
            "slurm", 4, 64, 1, 0, [], False, False, True, None, True, gpus_per_node=1
        )
        self.assertEqual(result["resource_layout"]["gpus"], 4)
        self.assertFalse(any("ranks/GPU" in w for w in result["warnings"]))

    def test_uneven_tasks_per_node_warns_and_keeps_float(self):
        # F3 regression: 5 tasks / 2 nodes is non-divisible -> warn + float value.
        result = hpc.diagnose_hpc(
            "slurm", 2, 5, 1, 0, [], False, False, False, None, True
        )
        self.assertEqual(result["resource_layout"]["tasks_per_node"], 2.5)
        self.assertTrue(any("evenly divisible" in w for w in result["warnings"]))

    def test_resource_count_cap_rejected(self):
        # Security: out-of-range resource counts exit via ValueError (exit code 2 in CLI).
        with self.assertRaisesRegex(ValueError, "nodes"):
            hpc.diagnose_hpc("slurm", 2_000_000, 1, 1, 0, [], False, False, False, None, False)

    def test_human_readable_output_includes_warnings(self):
        # F4 regression: non-JSON mode must surface warnings and a layout summary.
        import io
        import sys as _sys

        results = hpc.diagnose_hpc(
            "slurm", 1, 128, 1, 0, [], False, True, False, None, False
        )
        buf = io.StringIO()
        old = _sys.stdout
        try:
            _sys.stdout = buf
            hpc._print_human_readable(results)
        finally:
            _sys.stdout = old
        out = buf.getvalue()
        self.assertIn("RESOURCE LAYOUT", out)
        self.assertIn("WARNINGS", out)
        self.assertIn("OpenMP", out)


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
