# Simulation Orchestrator Examples

This directory contains examples demonstrating the simulation-orchestrator skill.

## Files

- `base_config.json` - Example base configuration for parameter sweeps
- `run_sweep.sh` - Generate parameter sweep configurations

## Quick Start

```bash
# Generate a 3x2 parameter sweep (dt and kappa)
bash examples/simulation-orchestrator/run_sweep.sh

# Or run directly:
python skills/simulation-workflow/simulation-orchestrator/scripts/sweep_generator.py \
    --base-config examples/simulation-orchestrator/base_config.json \
    --params "dt:0.001:0.01:3" \
    --method linspace \
    --output-dir ./my_sweep \
    --json
```

## Workflow Example

1. **Generate sweep**:
   ```bash
   python scripts/sweep_generator.py --base-config base.json --params "dt:1e-4:1e-2:5" --output-dir sweep1
   ```

2. **Initialize campaign**:
   ```bash
   python scripts/campaign_manager.py --action init --config-dir sweep1 --command "python sim.py --config {config}"
   ```

3. **Run simulations** (externally, e.g., with GNU parallel):
   ```bash
   parallel python sim.py --config {} ::: sweep1/config_*.json
   ```

4. **Track status**:
   ```bash
   python scripts/job_tracker.py --campaign-dir sweep1 --update
   ```

5. **Aggregate results**:
   ```bash
   python scripts/result_aggregator.py --campaign-dir sweep1 --metric objective --json
   ```
