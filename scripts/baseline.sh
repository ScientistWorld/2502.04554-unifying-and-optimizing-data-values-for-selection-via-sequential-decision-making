#!/bin/bash
# Run a baseline method from the paper.
#
# Baselines are simple reference methods the paper compares against. 
# Implement this only if applicable, i.e. the paper has baselines.
# You do not need to implement all baselines to begin — 
# just enough to validate that the evaluation pipeline works 
# and provide a reference point. You can decide to expand more baselines later.
# Each baseline must be actually run and scored through evaluate.sh
# so the numbers are verified, not self-reported.
# You can decide what this baseline script should do yourself.
#
# Usage:
#   bash scripts/baseline.sh <name>

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

BASELINE=${1:-random}
shift || true
DATASETS=("${@:-digits synthetic_planes}")
SEEDS=${SEEDS:-"10 20 30"}

mkdir -p checkpoints/rankings

for dataset in ${DATASETS[@]}; do
  for seed in ${SEEDS}; do
    case "$BASELINE" in
      random)
        python -m baseline.random_selection \
          --dataset "$dataset" \
          --seed "$seed" \
          --output-dir checkpoints/rankings
        ;;
      loo)
        python -m baseline.loo_selection \
          --dataset "$dataset" \
          --seed "$seed" \
          --output-dir checkpoints/rankings
        ;;
      datashap)
        python -m baseline.datashap_selection \
          --dataset "$dataset" \
          --seed "$seed" \
          --output-dir checkpoints/rankings
        ;;
      *)
        echo "Unknown baseline: $BASELINE" >&2
        exit 2
        ;;
    esac
  done
done

if [ "${EVALUATE_AFTER_RUN:-1}" = "1" ]; then
  bash scripts/evaluate.sh
fi
