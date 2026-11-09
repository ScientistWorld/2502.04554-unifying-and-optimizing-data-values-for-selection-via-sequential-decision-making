#!/bin/bash
# Standard visible evaluation -> scoring/scores.json.
#
# Builds the visible development instances (data/tasks.py, seeds 1-20 for
# each dataset), runs every ranker in scripts/rankers/*.sh on them through the
# ranker contract (data/instances.py), validates each ranking, retrains the
# fixed logistic-regression learner on every prefix and scores the test
# accuracy selection curve. Only rankings are read from rankers.
#
# Usage:
#   bash scripts/evaluate.sh                    # run all rankers and score
#   bash scripts/evaluate.sh --skip-run         # rescore existing rankings
#   bash scripts/evaluate.sh --rankers bipartite random
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."
# One BLAS/OpenMP thread per process unless the caller says otherwise: jobs get
# one CPU, and default per-core thread pools oversubscribe it badly.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-1} MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}

mkdir -p scoring
python -m eval.train.evaluate --scores scoring/scores.json --curves-dir scoring/curves "$@"
