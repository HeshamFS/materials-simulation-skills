"""Generate a deterministic resource header for PBS Professional and OpenPBS."""

import argparse
import json
import re


def build_header(
    *,
    job_name: str,
    walltime: str,
    nodes: int = 1,
    ntasks_per_node: int = 1,
    cpus_per_task: int = 1,
    mem_gb: int | None = None,
    queue: str | None = None,
) -> dict[str, str | list[str]]:
    """Map a uniform MPI/OpenMP resource request to PBS directives."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", job_name):
        raise ValueError("job-name must start with a letter and contain only letters, digits, _ and -")
    if queue is not None and not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*", queue):
        raise ValueError("queue must start with a letter or digit and contain only letters, digits, ., _ and -")

    match = re.fullmatch(r"([0-9]+):([0-5][0-9]):([0-5][0-9])", walltime)
    if not match:
        raise ValueError("time must be HH:MM:SS")
    hours, minutes, seconds = map(int, match.groups())
    if not (hours or minutes or seconds):
        raise ValueError("time must be greater than zero")

    for key, count in (
        ("nodes", nodes),
        ("ntasks-per-node", ntasks_per_node),
        ("cpus-per-task", cpus_per_task),
        ("mem-gb", mem_gb),
    ):
        if count is None and key == "mem-gb":
            continue
        if type(count) is not int or count <= 0:
            raise ValueError(f"{key} must be a positive integer")

    ncpus = ntasks_per_node * cpus_per_task
    select = f"{nodes}:ncpus={ncpus}:mpiprocs={ntasks_per_node}:ompthreads={cpus_per_task}"
    if mem_gb is not None:
        select += f":mem={mem_gb}gb"
    directives = [
        f"#PBS -N {job_name}",
        f"#PBS -l select={select}",
        f"#PBS -l walltime={hours:02d}:{minutes:02d}:{seconds:02d}",
    ]
    if queue is not None:
        directives.append(f"#PBS -q {queue}")
    header = "\n".join(["#!/bin/bash", *directives, ""])
    return {"header": header, "directives": directives}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-name", required=True, help="PBS job name")
    parser.add_argument("--time", required=True, dest="walltime", help="Walltime as HH:MM:SS")
    parser.add_argument("--nodes", type=int, default=1, help="Number of identical resource chunks")
    parser.add_argument("--ntasks-per-node", type=int, default=1, help="MPI ranks per chunk")
    parser.add_argument("--cpus-per-task", type=int, default=1, help="OpenMP threads per MPI rank")
    parser.add_argument("--mem-gb", type=int, help="Memory in GB per chunk")
    parser.add_argument("--queue", help="Optional local PBS queue")
    parser.add_argument("--json", action="store_true", help="Return a structured result")
    args = vars(parser.parse_args())
    as_json = args.pop("json")
    try:
        results = build_header(**args)
    except ValueError as exc:
        parser.error(str(exc))
    if as_json:
        print(json.dumps({"results": results}))
    else:
        print(results["header"], end="")


if __name__ == "__main__":
    main()
