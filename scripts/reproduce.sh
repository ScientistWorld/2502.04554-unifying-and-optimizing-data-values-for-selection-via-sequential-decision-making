#!/bin/bash
# Reproduce the reference results end-to-end (CPU only, no downloads needed).
#
# 1. Visible slice: run every ranker in scripts/rankers/ (the paper's method
#    and the random / leave-one-out / Data Shapley baselines) on the visible
#    instances -> scoring/scores_train.json, then rescore the same rankings
#    into scoring/scores.json.
# 2. Held-out slice: scripts/evaluate_test.sh -> scoring/scores_test.json.
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

rm -rf checkpoints/instances checkpoints/rankings scoring/curves scoring/curves_train
rm -f scoring/scores.json scoring/scores_train.json scoring/scores_test.json

bash scripts/evaluate_train.sh
bash scripts/evaluate.sh --skip-run
bash scripts/evaluate_test.sh
