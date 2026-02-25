import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "skills"
    / "hpc-deployment"
    / "slurm-job-script-generator"
    / "scripts"
    / "slurm_script_generator.py"
)


class TestSlurmScriptGeneratorCli(unittest.TestCase):
    def run_cmd(self, args):
        return subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_json_payload_contains_script(self):
        cmd = [
            str(SCRIPT),
            "--job-name",
            "phasefield",
            "--time",
            "00:10:00",
            "--nodes",
            "1",
            "--ntasks",
            "4",
            "--cpus-per-task",
            "2",
            "--mem",
            "8G",
            "--json",
            "--",
            "/bin/echo",
            "hello",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("inputs", payload)
        self.assertIn("results", payload)
        self.assertIn("script", payload["results"])
        self.assertIn("#SBATCH --job-name=phasefield", payload["results"]["script"])

    def test_writes_out_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "job.sbatch"
            cmd = [
                str(SCRIPT),
                "--job-name",
                "phasefield",
                "--time",
                "00:10:00",
                "--nodes",
                "1",
                "--ntasks-per-node",
                "2",
                "--cpus-per-task",
                "1",
                "--out",
                str(out),
                "--",
                "/bin/echo",
                "hello",
            ]
            result = self.run_cmd(cmd)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(out.exists())
            text = out.read_text()
            self.assertIn("#SBATCH --ntasks-per-node=2", text)

    def test_invalid_nodes_returns_exit_2(self):
        cmd = [
            str(SCRIPT),
            "--job-name",
            "phasefield",
            "--time",
            "00:10:00",
            "--nodes",
            "0",
            "--",
            "/bin/echo",
            "hello",
        ]
        result = self.run_cmd(cmd)
        self.assertEqual(result.returncode, 2)
        self.assertIn("nodes must be positive", result.stderr)


if __name__ == "__main__":
    unittest.main()

