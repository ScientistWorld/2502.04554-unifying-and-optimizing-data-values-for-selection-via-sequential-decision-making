#!/bin/bash
# Visible train-slice evaluator -> scoring/scores_train.json and
# scoring/curves_train/<method>.json. Runs every ranker in scripts/rankers/
# on the visible instances (seeds 1-20 per dataset) and scores them.
# Accepts the same options as scripts/evaluate.sh (e.g. --skip-run).
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."
# One BLAS/OpenMP thread per process unless the caller says otherwise: jobs get
# one CPU, and default per-core thread pools oversubscribe it badly.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-1} MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}

mkdir -p scoring
python -m eval.train.evaluate \
  --scores scoring/scores_train.json \
  --curves-dir scoring/curves_train \
  "$@"
