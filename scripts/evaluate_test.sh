#!/bin/bash
# Held-out test-slice evaluator -> scoring/scores_test.json.
#
# Runs with no arguments. Draws the held-out instances inside eval/test/,
# runs every ranker in scripts/rankers/*.sh on their inputs, and scores every
# method. Any failed ranker or invalid/missing ranking fails the run (non-zero
# exit, no scores file).
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."
# One BLAS/OpenMP thread per process unless the caller says otherwise: jobs get
# one CPU, and default per-core thread pools oversubscribe it badly.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-1} MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}

mkdir -p scoring
python -m eval.test.evaluate --scores scoring/scores_test.json "$@"
