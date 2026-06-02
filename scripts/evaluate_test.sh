#!/bin/bash
# Held-out test-slice evaluator. Mirrors scripts/evaluate.sh but writes
# scoring/scores_test.json and test-marked per-seed curve artifacts.

set -e

cd /home/user

mkdir -p scoring

python -m eval.test.evaluate \
  --scores scoring/scores_test.json \
  --curves-dir scoring/curves_test \
  "$@"
