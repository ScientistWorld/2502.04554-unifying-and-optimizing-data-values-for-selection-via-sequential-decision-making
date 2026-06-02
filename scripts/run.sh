#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

rm -rf scoring/curves_train scoring/curves_test
rm -f scoring/scores_train.json scoring/scores_test.json

bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
