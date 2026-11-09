#!/bin/bash
# Run the paper's method (bipartite-surrogate selector) on the visible
# development instances, writing checkpoints/rankings/train/bipartite/.
#
# Usage:
#   bash scripts/method.sh
#   EVALUATE_AFTER_RUN=0 bash scripts/method.sh
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

python -m data.instances checkpoints/instances/train
bash scripts/rankers/bipartite.sh "$PWD/checkpoints/instances/train" "$PWD/checkpoints/rankings/train/bipartite"

if [ "${EVALUATE_AFTER_RUN:-1}" = "1" ]; then
  bash scripts/evaluate.sh --skip-run --rankers bipartite
fi
