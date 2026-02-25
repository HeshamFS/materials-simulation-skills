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
