#!/bin/bash
# Visible train-slice evaluator. Mirrors scripts/evaluate.sh but writes
# scoring/scores_train.json and train-marked per-seed curve artifacts.

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

mkdir -p scoring

python -m eval.train.evaluate \
  --scores scoring/scores_train.json \
  --curves-dir scoring/curves_train \
  "$@"
