#!/bin/bash
set -euo pipefail

cd /home/user

rm -rf scoring/curves_train scoring/curves_test
rm -f scoring/scores_train.json scoring/scores_test.json

bash scripts/evaluate_train.sh
bash scripts/evaluate_test.sh
