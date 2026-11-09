#!/bin/bash
# Job entry point: reproduce the reference end to end (visible slice and the
# held-out test for every ranker in scripts/rankers/) and validate.
#
# The hardening checks are a separate, optional step (about 1.5 h on one CPU):
#   python -m redteam.hardening.harness --force && python -m redteam.hardening.summarize
set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."
# One BLAS/OpenMP thread per process unless the caller says otherwise: jobs get
# one CPU, and default per-core thread pools oversubscribe it badly.
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-1} OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-1} MKL_NUM_THREADS=${MKL_NUM_THREADS:-1}

echo "== $(date -u +%FT%TZ) reproduce (visible + held-out)"
bash scripts/reproduce.sh || { echo "reproduce failed"; exit 1; }

echo "== $(date -u +%FT%TZ) validate"
python validate.py --compare --post-design
echo "== $(date -u +%FT%TZ) done"
