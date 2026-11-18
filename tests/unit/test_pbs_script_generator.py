import pytest

from tests.unit._utils import load_module


pbs = load_module(
    "pbs_script_generator",
    "skills/hpc-deployment/pbs-job-script-generator/scripts/pbs_script_generator.py",
)


def test_single_chunk_header():
    output = pbs.build_header(job_name="run", walltime="0:15:00")
    assert output["directives"] == [
        "#PBS -N run",
        "#PBS -l select=1:ncpus=1:mpiprocs=1:ompthreads=1",
        "#PBS -l walltime=00:15:00",
    ]
    assert output["header"] == "\n".join(["#!/bin/bash", *output["directives"], ""])


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"job_name": "bad name"}, "job-name"),
        ({"queue": "bad queue"}, "queue"),
        ({"walltime": "01:60:00"}, "HH:MM:SS"),
        ({"walltime": "00:00:00"}, "greater than zero"),
        ({"cpus_per_task": 0}, "cpus-per-task"),
        ({"mem_gb": float("inf")}, "mem-gb"),
    ],
)
def test_invalid_resources(overrides, message):
    defaults = {"job_name": "run", "walltime": "00:15:00"}
    with pytest.raises(ValueError, match=message):
        pbs.build_header(**{**defaults, **overrides})
