import json
import subprocess
import sys
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills/hpc-deployment/pbs-job-script-generator/scripts/pbs_script_generator.py"
)


def test_pbs_cli_equivalent_text_and_json():
    args = [
        sys.executable, str(SCRIPT), "--job-name", "hybrid", "--time", "25:00:00",
        "--nodes", "2", "--ntasks-per-node", "4", "--cpus-per-task", "8", "--mem-gb", "32",
    ]
    result = subprocess.run(args, text=True, capture_output=True, check=True)
    structured = subprocess.run([*args, "--json"], text=True, capture_output=True, check=True)
    output = json.loads(structured.stdout)["results"]
    assert result.stdout == output["header"]
    assert "#PBS -l select=2:ncpus=32:mpiprocs=4:ompthreads=8:mem=32gb" in output["directives"]
    assert "#PBS -l walltime=25:00:00" in output["directives"]


def test_pbs_cli_invalid_memory_returns_usage_error():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--job-name", "run", "--time", "00:10:00", "--mem-gb", "0"],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 2
    assert "mem-gb must be a positive integer" in result.stderr
    assert not result.stdout
