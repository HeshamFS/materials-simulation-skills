---
name: slurm-job-script-generator
description: >
  Generate correct, copy-pasteable SLURM sbatch job scripts and sanity-check
  HPC resource requests — configure nodes, MPI tasks, OpenMP threads, memory
  (per-node or per-cpu), GPUs, walltime, partitions, modules, and environment
  variables, with automatic detection of conflicting directives and
  oversubscription. Use when preparing a SLURM submission script, deciding
  between pure MPI and hybrid MPI+OpenMP layouts, standardizing #SBATCH
  directives across a team, debugging why a job won't launch or gets killed,
  or setting up GPU-accelerated simulation jobs, even if the user only says
  "I need to run this on the cluster" or "my job keeps getting killed."
allowed-tools: Read, Bash, Write, Grep, Glob
metadata:
  author: HeshamFS
  version: "1.1.0"
  security_tier: high
  security_reviewed: true
  tested_with:
    - claude-code
    - gemini-cli
    - vs-code-copilot
  eval_cases: 2
  last_reviewed: "2026-03-26"
---

# SLURM Job Script Generator

## Goal

Generate a correct, copy-pasteable SLURM job script (`.sbatch`) for running a simulation, and surface common configuration mistakes (bad walltime format, conflicting memory flags, oversubscription hints).

## Requirements

- Python 3.8+
- No external dependencies (Python standard library only)
- Works on Linux, macOS, and Windows (script generation only)

## Inputs to Gather

| Input | Description | Example |
|-------|-------------|---------|
| Job name | Short identifier for the job | `phasefield-strong-scaling` |
| Walltime | SLURM time limit | `00:30:00` |
| Partition | Cluster partition/queue (if required) | `compute` |
| Account | Project/account (if required) | `matsim` |
| Nodes | Number of nodes to allocate | `2` |
| MPI tasks | Total tasks, or tasks per node | `128` or `64` per node |
| Threads | CPUs per task (OpenMP threads) | `2` |
| Memory | `--mem` or `--mem-per-cpu` (cluster policy dependent) | `32G` |
| GPUs | GPUs per node (optional) | `4` |
| Working directory | Where the run should execute | `$SLURM_SUBMIT_DIR` |
| Modules | Environment modules to load (optional) | `gcc/12`, `openmpi/4.1` |
| Run command | The command to launch under SLURM | `./simulate --config cfg.json` |

## Decision Guidance

### MPI vs MPI+OpenMP layout

```
Does the code use OpenMP / threading?
├── NO  → Use MPI-only: cpus-per-task=1
└── YES → Use hybrid: set cpus-per-task = threads per MPI rank
          and export OMP_NUM_THREADS = cpus-per-task
```

**Rule of thumb:** if you see diminishing strong-scaling efficiency at high MPI ranks, try fewer ranks with more threads per rank (and measure).

### Memory flag selection

- Use **either** `--mem` (per node) **or** `--mem-per-cpu` (per CPU), not both.
- Follow your cluster’s documentation; some sites enforce one style.
- SLURM `--mem` units are integer MB by default, or an integer with suffix `K/M/G/T` (and `--mem=0` commonly means “all memory on node”).

## Script Outputs (JSON Fields)

| Script | Key Outputs |
|--------|-------------|
| `scripts/slurm_script_generator.py` | `results.script`, `results.directives`, `results.derived`, `results.warnings` |

## Workflow

1. Gather cluster constraints (partition/account, GPU policy, memory policy).
2. Choose a process layout (MPI-only vs hybrid MPI+OpenMP).
3. Generate the script with `slurm_script_generator.py`.
4. Inspect warnings (conflicts, suspicious layouts).
5. Save the generated script as `job.sbatch`.
6. Submit with `sbatch job.sbatch` and monitor with `squeue`.

## CLI Examples

```bash
# Preview a job script (prints to stdout)
python3 skills/hpc-deployment/slurm-job-script-generator/scripts/slurm_script_generator.py \
  --job-name phasefield \
  --time 00:10:00 \
  --partition compute \
  --nodes 1 \
  --ntasks-per-node 8 \
  --cpus-per-task 2 \
  --mem 16G \
  --module gcc/12 \
  --module openmpi/4.1 \
  -- \
  ./simulate --config config.json

# Write to a file and also emit structured JSON
python3 skills/hpc-deployment/slurm-job-script-generator/scripts/slurm_script_generator.py \
  --job-name phasefield \
  --time 00:10:00 \
  --nodes 1 \
  --ntasks 16 \
  --cpus-per-task 1 \
  --out job.sbatch \
  --json \
  -- \
  /bin/echo hello
```

## Conversational Workflow Example

**User**: I need an `sbatch` script for my MPI simulation. I want 2 nodes, 64 ranks per node, 2 OpenMP threads per rank, and 2 hours.

**Agent workflow**:
1. Confirm partition/account and whether GPUs are needed.
2. Generate a hybrid job script:
   ```bash
   python3 scripts/slurm_script_generator.py --job-name run --time 02:00:00 --nodes 2 --ntasks-per-node 64 --cpus-per-task 2 -- -- ./simulate
   ```
3. Explain the mapping:
   - Total ranks = 128
   - Threads per rank = 2 (`OMP_NUM_THREADS=2`)
4. If the user provides node core counts, sanity-check oversubscription using `--cores-per-node`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| `time must be HH:MM:SS or D-HH:MM:SS` | Bad walltime format | Use `00:30:00` or `1-00:00:00` |
| `nodes must be positive` | Non-positive nodes | Provide `--nodes >= 1` |
| `Provide either --mem or --mem-per-cpu, not both` | Conflicting memory directives | Choose one memory style |
| `Provide a run command after --` | Missing launch command | Add `-- ./simulate ...` |

## Security

### Input Validation
- `--time` is validated against strict `HH:MM:SS` or `D-HH:MM:SS` format via regex
- `--nodes`, `--ntasks`, `--ntasks-per-node`, `--cpus-per-task`, `--gpus` are validated as positive integers with upper bounds
- `--mem` and `--mem-per-cpu` are validated against SLURM's accepted format (`<int>[K|M|G|T]`); providing both simultaneously is rejected
- `--job-name` is validated against `[a-zA-Z0-9_.-]+` (no shell metacharacters)
- `--partition` and `--account` are validated against safe-character allowlists
- `--module` values are validated to prevent shell injection (no `;`, `|`, `&`, backticks, or `$`)

### File Access
- The script reads no external files; all inputs are provided via CLI arguments
- `--out` writes the generated sbatch script to a single specified file path
- The generated script is a plain-text shell script with `#SBATCH` directives; it contains no dynamically generated code

### Tool Restrictions
- **Read**: Used to inspect script source, references, and existing job scripts
- **Bash**: Used to execute `slurm_script_generator.py` with explicit argument lists; the generated script itself is NOT executed by the agent
- **Write**: Used to save the generated `.sbatch` file; writes are scoped to the user's working directory
- **Grep/Glob**: Used to locate existing scripts, configs, and cluster documentation

### Safety Measures
- No `eval()`, `exec()`, or dynamic code generation
- All subprocess calls use explicit argument lists (no `shell=True`)
- The run command (after `--`) is included verbatim in the generated script but is never executed by the skill itself
- Module names are sanitized to prevent injection into `module load` directives
- Generated scripts use `set -euo pipefail` for safe shell execution on the cluster

## Limitations

- Does not query cluster hardware or site policies; it can only validate internal consistency.
- SLURM installations vary (GPU directives, QoS rules, partitions). Adjust directives for your site.

## References

- `references/slurm_directives.md` - Common `#SBATCH` directives and mapping tips

## Version History

- **v1.0.0** (2026-02-25): Initial SLURM job script generator
