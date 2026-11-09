#!/bin/bash
# Run one baseline ranker (random | loo | datashap) on the visible
# development instances, writing checkpoints/rankings/train/<name>/.
#
# Usage:
#   bash scripts/baseline.sh <name>
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

BASELINE=${1:-random}
if [ ! -f "scripts/rankers/${BASELINE}.sh" ]; then
  echo "Unknown baseline: $BASELINE (expected a ranker in scripts/rankers/)" >&2
  exit 2
fi

python -m data.instances checkpoints/instances/train
bash "scripts/rankers/${BASELINE}.sh" "$PWD/checkpoints/instances/train" "$PWD/checkpoints/rankings/train/${BASELINE}"

if [ "${EVALUATE_AFTER_RUN:-1}" = "1" ]; then
  bash scripts/evaluate.sh --skip-run --rankers "$BASELINE"
fi
