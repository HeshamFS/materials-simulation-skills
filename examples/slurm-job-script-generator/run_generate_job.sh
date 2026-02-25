#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

OUT="$(mktemp -t slurm_job_XXXXXX.sbatch)"
trap 'rm -f "$OUT"' EXIT

python3 "$ROOT_DIR/skills/hpc-deployment/slurm-job-script-generator/scripts/slurm_script_generator.py" \
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
  /bin/echo hello > "$OUT"

echo "Generated: $OUT"
echo ""
echo "=== Script preview ==="
sed -n '1,80p' "$OUT"

