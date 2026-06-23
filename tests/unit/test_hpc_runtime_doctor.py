"""Unit tests for the hpc-runtime-doctor skill script.

Locks in the v1.1.0 fixes:
- F1: unit-consistent ranks-per-GPU warning (total ranks / total GPUs) and
  the new --gpus-per-node argument.
- F3: integer tasks_per_node when divisible, float + warning when uneven.
- F4: full human-readable (non-JSON) output.
- Security: resource-count, symptom, and walltime caps.
"""
import io
import sys
import unittest

from tests.unit._utils import load_module


hpc = load_module(
    "hpc_runtime_doctor",
    "skills/hpc-deployment/hpc-runtime-doctor/scripts/hpc_runtime_doctor.py",
)


def diag(**kwargs):
    defaults = dict(
        scheduler="slurm",
        nodes=1,
        tasks=1,
        cpus_per_task=1,
        gpus=0,
        symptoms=[],
        uses_mpi=False,
        uses_openmp=False,
        uses_gpu=False,
        walltime=None,
        scratch=True,
    )
    defaults.update(kwargs)
    return hpc.diagnose_hpc(**defaults)


class TestRanksPerGpu(unittest.TestCase):
    def test_multinode_oversubscription_warns(self):
        # 512 ranks / 4 GPUs = 128 ranks/GPU. The old per-node-vs-total rule missed it.
        result = diag(nodes=8, tasks=512, gpus=4, uses_gpu=True)
        self.assertTrue(any("ranks/GPU" in w for w in result["warnings"]))

    def test_skill_workflow_example_warns(self):
        # SKILL.md workflow example: 128 ranks / 4 GPUs = 32 ranks/GPU.
        result = diag(nodes=2, tasks=128, gpus=4, cpus_per_task=2, uses_gpu=True)
        self.assertTrue(any("32.0 ranks/GPU" in w for w in result["warnings"]))

    def test_threshold_boundary_no_warning(self):
        # Exactly 16 ranks/GPU must NOT warn (threshold is strictly > 16).
        result = diag(nodes=4, tasks=64, gpus=4, uses_gpu=True)
        self.assertFalse(any("ranks/GPU" in w for w in result["warnings"]))

    def test_gpus_per_node_overrides_and_scales(self):
        result = diag(nodes=4, tasks=64, gpus=99, gpus_per_node=1, uses_gpu=True)
        self.assertEqual(result["resource_layout"]["gpus"], 4)
        self.assertEqual(result["resource_layout"]["gpus_per_node"], 1)

    def test_uses_gpu_without_gpus_warns(self):
        result = diag(nodes=1, tasks=4, gpus=0, uses_gpu=True)
        self.assertTrue(any("no GPUs are allocated" in w for w in result["warnings"]))


class TestTasksPerNode(unittest.TestCase):
    def test_divisible_is_int(self):
        result = diag(nodes=2, tasks=128)
        self.assertEqual(result["resource_layout"]["tasks_per_node"], 64)
        self.assertIsInstance(result["resource_layout"]["tasks_per_node"], int)

    def test_uneven_keeps_float_and_warns(self):
        result = diag(nodes=2, tasks=5)
        self.assertEqual(result["resource_layout"]["tasks_per_node"], 2.5)
        self.assertTrue(any("evenly divisible" in w for w in result["warnings"]))


class TestHumanReadable(unittest.TestCase):
    def _capture(self, results):
        buf = io.StringIO()
        old = sys.stdout
        try:
            sys.stdout = buf
            hpc._print_human_readable(results)
        finally:
            sys.stdout = old
        return buf.getvalue()

    def test_no_symptoms_not_silent(self):
        out = self._capture(diag(nodes=1, tasks=4))
        self.assertIn("RESOURCE LAYOUT", out)
        self.assertIn("No symptoms supplied", out)
        self.assertIn("ENVIRONMENT CHECKS", out)
        self.assertIn("RETRY PLAN", out)

    def test_warnings_surface(self):
        out = self._capture(diag(nodes=1, tasks=128, cpus_per_task=1, uses_openmp=True))
        self.assertIn("WARNINGS", out)
        self.assertIn("OpenMP", out)


class TestSecurityCaps(unittest.TestCase):
    def test_resource_count_cap(self):
        with self.assertRaisesRegex(ValueError, "nodes"):
            diag(nodes=2_000_000, tasks=1)

    def test_negative_rejected(self):
        with self.assertRaisesRegex(ValueError, "non-negative"):
            diag(nodes=1, tasks=1, gpus=-1)

    def test_walltime_length_cap(self):
        with self.assertRaisesRegex(ValueError, "walltime"):
            diag(nodes=1, tasks=1, walltime="x" * 40)

    def test_too_many_symptoms(self):
        with self.assertRaisesRegex(ValueError, "too many symptoms"):
            hpc._split_symptoms(",".join(["s"] * 70))

    def test_symptom_too_long(self):
        with self.assertRaisesRegex(ValueError, "exceeds"):
            hpc._split_symptoms("x" * 80)


if __name__ == "__main__":
    unittest.main()
