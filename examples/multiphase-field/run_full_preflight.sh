#!/usr/bin/env bash
set -euo pipefail

bash "$(dirname "$0")/run_stability_precheck.sh"
bash "$(dirname "$0")/run_stability_adjusted.sh"
bash "$(dirname "$0")/run_integration_selector.sh"
bash "$(dirname "$0")/run_error_norm_multifield.sh"
bash "$(dirname "$0")/run_adaptive_step_reject.sh"
bash "$(dirname "$0")/run_matrix_condition_coupled.sh"
