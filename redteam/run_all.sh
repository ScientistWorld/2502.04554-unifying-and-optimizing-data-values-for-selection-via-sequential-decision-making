#!/bin/bash
set -euo pipefail
cd /home/user
# Thread limits keep the small independent fits from oversubscribing the node.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
for name in \
  reference_seed0 reference_seed1 reference_seed2 \
  weaker_random weaker_label_blocks \
  better_coverage_reset better_validation_prototypes shortcut_more_samples \
  shortcut_forged_fields shortcut_invalid_empty shortcut_invalid_constant \
  shortcut_invalid_impossible shortcut_singleton_constant shortcut_larger_pool shortcut_replaced_task \
  shortcut_seed_cherry_pick shortcut_brute_force shortcut_rebuilt_answers; do
  if [ -f "redteam/$name/run_record.json" ]; then
    echo "Already attempted: $name (remove its record to rerun)"
    continue
  fi
  bash "redteam/$name/run.sh"
done
python -m redteam.summarize
