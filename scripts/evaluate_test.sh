#!/bin/bash
# Held-out test-slice evaluator. Mirrors scripts/evaluate.sh but writes
# scoring/scores_test.json and test-marked per-seed curve artifacts.

set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

mkdir -p scoring

python -m eval.test.evaluate \
  --scores scoring/scores_test.json \
  --curves-dir scoring/curves_test \
  "$@"
