#!/bin/bash
# Run the paper's proposed method.
#
# This script trains/runs the paper's method using code in method/.
#
# Usage:
#   bash scripts/method.sh

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

DATASETS=("${@:-digits synthetic_planes}")
SEEDS=${SEEDS:-"1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20"}

mkdir -p checkpoints/rankings

for dataset in ${DATASETS[@]}; do
  for seed in ${SEEDS}; do
    python -m method.bipartite_selection \
      --dataset "$dataset" \
      --seed "$seed" \
      --output-dir checkpoints/rankings
  done
done

if [ "${EVALUATE_AFTER_RUN:-1}" = "1" ]; then
  bash scripts/evaluate.sh
fi
