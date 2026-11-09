#!/bin/bash
# Visible train-slice evaluator -> scoring/scores_train.json and
# scoring/curves_train/<method>.json. Runs every ranker in scripts/rankers/
# on the visible instances (seeds 1-20 per dataset) and scores them.
# Accepts the same options as scripts/evaluate.sh (e.g. --skip-run).
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

mkdir -p scoring
python -m eval.train.evaluate \
  --scores scoring/scores_train.json \
  --curves-dir scoring/curves_train \
  "$@"
