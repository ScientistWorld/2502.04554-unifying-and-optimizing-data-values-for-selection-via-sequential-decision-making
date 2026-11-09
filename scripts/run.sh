#!/bin/bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

rm -rf checkpoints/rankings scoring/curves scoring/curves_train scoring/curves_test
rm -f scoring/scores.json scoring/scores_train.json scoring/scores_test.json

bash scripts/reproduce.sh
python validate.py --compare
bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
python validate.py --compare
