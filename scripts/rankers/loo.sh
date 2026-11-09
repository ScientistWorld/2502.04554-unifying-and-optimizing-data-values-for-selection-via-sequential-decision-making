#!/bin/bash
# Ranker: Leave-one-out baseline.
# Contract (see data/instances.py): bash scripts/rankers/loo.sh INSTANCES_DIR OUTPUT_DIR
# writes OUTPUT_DIR/<instance_id>.json = {"ranking": [...]} for every instance.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec python -m baseline.loo_selection --instances "$1" --output-dir "$2"
