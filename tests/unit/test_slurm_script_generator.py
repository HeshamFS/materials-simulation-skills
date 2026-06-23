import unittest

from tests.unit._utils import load_module


class TestSlurmScriptGenerator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_module(
            "slurm_script_generator",
            "skills/hpc-deployment/slurm-job-script-generator/scripts/slurm_script_generator.py",
        )

    def test_walltime_normalization(self):
        self.assertEqual(self.mod._normalize_walltime("00:10:00"), "00:10:00")
        self.assertEqual(self.mod._normalize_walltime("1-2:03:04"), "1-02:03:04")

    def test_build_resources_ntasks_per_node_derives_ntasks(self):
        r = self.mod.build_resources(
            nodes=2,
            ntasks=None,
            ntasks_per_node=64,
            cpus_per_task=2,
            mem="32G",
            mem_per_cpu=None,
            gpus_per_node=None,
            gpu_type=None,
        )
        self.assertEqual(r["ntasks"], 128)
        self.assertEqual(r["ntasks_per_node"], 64)
        self.assertEqual(r["cpus_per_task"], 2)

    def test_mem_flags_conflict(self):
        with self.assertRaises(ValueError):
            self.mod.build_resources(
                nodes=1,
                ntasks=1,
                ntasks_per_node=None,
                cpus_per_task=1,
                mem="16G",
                mem_per_cpu="2G",
                gpus_per_node=None,
                gpu_type=None,
            )

    def test_invalid_mem_units_rejected(self):
        with self.assertRaises(ValueError):
            self.mod.build_resources(
                nodes=1,
                ntasks=1,
                ntasks_per_node=None,
                cpus_per_task=1,
                mem="16GB",
                mem_per_cpu=None,
                gpus_per_node=None,
                gpu_type=None,
            )

    def test_generate_script_contains_directives_and_run_line(self):
        resources = self.mod.build_resources(
            nodes=1,
            ntasks=8,
            ntasks_per_node=None,
            cpus_per_task=2,
            mem="16G",
            mem_per_cpu=None,
            gpus_per_node=1,
            gpu_type="a100",
        )
        payload = self.mod.generate_sbatch_script(
            job_name="phasefield",
            time_limit="00:10:00",
            partition="compute",
            account=None,
            qos=None,
            constraint=None,
            reservation=None,
            exclusive=False,
            output="slurm-%j.out",
            error="slurm-%j.err",
            mail_user=None,
            mail_type=None,
            workdir="$SLURM_SUBMIT_DIR",
            modules=["gcc/12"],
            env=["FOO=bar"],
            launcher="srun",
            srun_extra=None,
            command=["/bin/echo", "hello"],
            resources=resources,
            cores_per_node=16,
        )
        script = payload["results"]["script"]
        self.assertIn("#SBATCH --job-name=phasefield", script)
        self.assertIn("#SBATCH --time=00:10:00", script)
        self.assertIn("#SBATCH --gres=gpu:a100:1", script)
        self.assertIn("export OMP_NUM_THREADS=2", script)
        self.assertIn("srun --ntasks=8 --cpus-per-task=2", payload["results"]["run_line"])

    def _basic_payload(self, **overrides):
        defaults = dict(
            nodes=1,
            ntasks=4,
            ntasks_per_node=None,
            cpus_per_task=1,
            mem=None,
            mem_per_cpu=None,
            gpus_per_node=None,
            gpu_type=None,
        )
        res_kwargs = {k: overrides.pop(k, v) for k, v in defaults.items()}
        resources = self.mod.build_resources(**res_kwargs)
        gen_defaults = dict(
            job_name="job",
            time_limit="00:10:00",
            partition=None,
            account=None,
            qos=None,
            constraint=None,
            reservation=None,
            exclusive=False,
            output=None,
            error=None,
            mail_user=None,
            mail_type=None,
            workdir=None,
            modules=[],
            env=[],
            launcher="srun",
            srun_extra=None,
            command=["./sim"],
            cores_per_node=None,
        )
        gen_defaults.update(overrides)
        return self.mod.generate_sbatch_script(resources=resources, **gen_defaults)

    def test_directives_precede_first_executable_command(self):
        # Regression for F1: every #SBATCH line must appear before the first
        # non-comment, non-blank line (SLURM stops parsing directives after it).
        payload = self._basic_payload()
        script_lines = payload["results"]["script"].splitlines()
        first_exec_idx = None
        for i, line in enumerate(script_lines):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            first_exec_idx = i
            break
        self.assertIsNotNone(first_exec_idx)
        # No #SBATCH directive may appear at or after the first executable line.
        for line in script_lines[first_exec_idx:]:
            self.assertFalse(line.strip().startswith("#SBATCH"))
        # And the first executable line should be `set -euo pipefail`.
        self.assertEqual(script_lines[first_exec_idx].strip(), "set -euo pipefail")

    def test_nested_launcher_not_double_wrapped(self):
        # Regression for F3: mpirun/srun command must not be wrapped in srun.
        for inner in (["mpirun", "./lammps"], ["srun", "./gpu_sim"], ["/usr/bin/mpiexec", "./x"]):
            payload = self._basic_payload(command=inner)
            run_line = payload["results"]["run_line"]
            self.assertFalse(
                run_line.startswith("srun --ntasks"),
                f"unexpected srun wrap for {inner}: {run_line}",
            )
            self.assertTrue(
                any("already starts with a launcher" in w for w in payload["results"]["warnings"]),
                f"missing double-launcher warning for {inner}",
            )

    def test_plain_command_is_wrapped_in_srun(self):
        payload = self._basic_payload(command=["./sim"])
        self.assertTrue(payload["results"]["run_line"].startswith("srun --ntasks=4"))
        self.assertEqual(payload["results"]["warnings"], [])

    def test_srun_extra_cannot_inject_shell(self):
        # Regression for F5: shell metacharacters in --srun-extra are neutralized.
        payload = self._basic_payload(srun_extra="--mpi=pmix; rm -rf /")
        run_line = payload["results"]["run_line"]
        # The semicolon must be quoted (literal arg), not a live command separator.
        self.assertNotIn("pmix; rm", run_line)
        self.assertIn("'--mpi=pmix;'", run_line)

    def test_gpu_ratio_warning_when_not_divisible(self):
        # F6/F7: ntasks not divisible by total GPUs -> warning + derived fields.
        payload = self._basic_payload(ntasks=30, gpus_per_node=4, command=["./gpu_sim"])
        derived = payload["results"]["derived"]
        self.assertEqual(derived["total_gpus"], 4)
        self.assertEqual(derived["ranks_per_gpu"], 7.5)
        self.assertTrue(
            any("task-to-gpu ratio is not an integer" in w.lower() for w in payload["results"]["warnings"])
        )

    def test_gpu_ratio_no_warning_when_divisible(self):
        payload = self._basic_payload(ntasks=32, gpus_per_node=4, command=["./gpu_sim"])
        self.assertEqual(payload["results"]["warnings"], [])

    def test_integer_upper_bounds_enforced(self):
        with self.assertRaises(ValueError):
            self.mod.build_resources(
                nodes=10**9,
                ntasks=1,
                ntasks_per_node=None,
                cpus_per_task=1,
                mem=None,
                mem_per_cpu=None,
                gpus_per_node=None,
                gpu_type=None,
            )

    def test_partition_allowlist_rejects_metacharacters(self):
        resources = self.mod.build_resources(
            nodes=1, ntasks=1, ntasks_per_node=None, cpus_per_task=1,
            mem=None, mem_per_cpu=None, gpus_per_node=None, gpu_type=None,
        )
        with self.assertRaises(ValueError):
            self.mod.generate_sbatch_script(
                job_name="job", time_limit="00:10:00", partition="evil;rm",
                account=None, qos=None, constraint=None, reservation=None,
                exclusive=False, output=None, error=None, mail_user=None,
                mail_type=None, workdir=None, modules=[], env=[],
                launcher="srun", srun_extra=None, command=["./sim"],
                resources=resources,
            )

    def test_module_allowlist_rejects_metacharacters(self):
        resources = self.mod.build_resources(
            nodes=1, ntasks=1, ntasks_per_node=None, cpus_per_task=1,
            mem=None, mem_per_cpu=None, gpus_per_node=None, gpu_type=None,
        )
        with self.assertRaises(ValueError):
            self.mod.generate_sbatch_script(
                job_name="job", time_limit="00:10:00", partition=None,
                account=None, qos=None, constraint=None, reservation=None,
                exclusive=False, output=None, error=None, mail_user=None,
                mail_type=None, workdir=None, modules=["gcc;evil"], env=[],
                launcher="srun", srun_extra=None, command=["./sim"],
                resources=resources,
            )
        # valid versioned module is accepted
        ok = self.mod.generate_sbatch_script(
            job_name="job", time_limit="00:10:00", partition=None,
            account=None, qos=None, constraint=None, reservation=None,
            exclusive=False, output=None, error=None, mail_user=None,
            mail_type=None, workdir=None, modules=["openmpi/4.1"], env=[],
            launcher="srun", srun_extra=None, command=["./sim"],
            resources=resources,
        )
        self.assertIn("module load openmpi/4.1", ok["results"]["script"])

    def test_cli_help_exits_zero(self):
        # Regression for F2: --help must not crash on the %j help strings.
        import subprocess
        import sys
        proc = subprocess.run(
            [sys.executable,
             "skills/hpc-deployment/slurm-job-script-generator/scripts/slurm_script_generator.py",
             "--help"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("slurm-%j.out", proc.stdout)

    def test_missing_command_is_validation_error(self):
        resources = self.mod.build_resources(
            nodes=1,
            ntasks=1,
            ntasks_per_node=None,
            cpus_per_task=1,
            mem=None,
            mem_per_cpu=None,
            gpus_per_node=None,
            gpu_type=None,
        )
        with self.assertRaises(ValueError):
            self.mod.generate_sbatch_script(
                job_name="job",
                time_limit="00:10:00",
                partition=None,
                account=None,
                qos=None,
                constraint=None,
                reservation=None,
                exclusive=False,
                output=None,
                error=None,
                mail_user=None,
                mail_type=None,
                workdir=None,
                modules=[],
                env=[],
                launcher="srun",
                srun_extra=None,
                command=[],
                resources=resources,
            )


if __name__ == "__main__":
    unittest.main()
