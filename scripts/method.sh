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
# One BLAS/OpenMP thread per process unless the caller says otherwise: jobs get
# one CPU, and default per-core thread pools oversubscribe it badly.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-1} MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}

python -m data.instances checkpoints/instances/train
bash scripts/rankers/bipartite.sh "$PWD/checkpoints/instances/train" "$PWD/checkpoints/rankings/train/bipartite"

if [ "${EVALUATE_AFTER_RUN:-1}" = "1" ]; then
  bash scripts/evaluate.sh --skip-run --rankers bipartite
fi
