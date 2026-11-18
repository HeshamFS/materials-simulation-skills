---
name: pbs-job-script-generator
description: >
  Generates PBS Professional and OpenPBS job headers with uniform MPI and
  OpenMP layouts. Use when translating a basic SLURM resource request to PBS
  or composing and checking PBS CPU, memory, walltime and queue directives.
allowed-tools: Read, Bash
metadata:
  version: "1.0.0"
  agent_evaluation_status: "not_revalidated"
  standards:
    - "PBS Professional and OpenPBS resource directives: https://docs.nvidia.com/base-command-manager/product-manuals/10/user/pbspro"
---

# PBS Job Script Generator

## Goal

Generate a PBS header for identical CPU resource chunks.

## Requirements

Python 3.10 or newer. Header generation needs no scheduler installation.

## Inputs to Gather

| Input | Meaning |
| --- | --- |
| `--job-name` | PBS job name |
| `--time` | Maximum job duration in HH:MM:SS |
| `--nodes` | Number of identical chunks |
| `--ntasks-per-node` | MPI ranks per chunk |
| `--cpus-per-task` | Threads per MPI rank |
| `--mem-gb` | Optional GB of memory per chunk |
| `--queue` | Optional local PBS queue |

## Decision Guidance

For a pure MPI job, use one thread per rank. For a hybrid job, request the MPI
rank count and threads per rank separately. Check local site policy for the
queue name, the resources per chunk and whether each chunk occupies one node.

## Script Outputs

| Script | Output | Meaning |
| --- | --- | --- |
| `scripts/pbs_script_generator.py` | `results.header` | Shebang and complete directives |
| same | `results.directives` | Directive lines in order |

## Workflow

1. Identify the target scheduler and collect the site's resource limits.
2. Generate the PBS header and check the chunk count, ranks and threads.
3. Append the user's existing workload commands after the directives.

## Verification checklist

- `ncpus` per chunk equals MPI ranks times threads per rank.
- `mem` is allocated per resource chunk and `walltime` applies to the job.
- PBS directives appear before the workload commands.

## Common pitfalls

Request the thread and rank counts separately. The number of CPUs per chunk
is neither the total CPU allocation nor the number of MPI ranks.

## CLI Examples

```bash
python skills/hpc-deployment/pbs-job-script-generator/scripts/pbs_script_generator.py \
  --job-name example --time 00:30:00 --nodes 2 --ntasks-per-node 4 \
  --cpus-per-task 8 --mem-gb 32 --queue compute --json
```

## Conversational Workflow Example

For two chunks with four MPI ranks and eight threads per rank, the request has
32 CPUs per chunk. Verify that the site's compute queue can provide this layout.

## Error Handling

Invalid arguments return status 2 with a description. Correct the requested
resource or ask for the site's allowed values.

## Limitations

The script emits a header only. Mixed chunks, GPUs, placement policies and site
accounting directives are outside its resource model.

## Security

### Input Validation

Identifier allowlists keep job and queue names on a single directive line.
Resource counts must be positive integers.

### File Access

The script writes the header to standard output and does not read or write
workload files.

### Tool Restrictions

Use the shell to run the header generator during planning. The generator
does not launch a scheduler command.

### Safety Measures

Check the generated resource limits and local queue policy before submitting
the completed script to a cluster.

## References

[PBS resource mapping and scheduler references](references/pbs_directives.md)

## Version History

- v1.0.0 (2026-11-18) — Initial PBS header generator.
