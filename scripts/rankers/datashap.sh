#!/bin/bash
# Ranker: Monte Carlo Data Shapley baseline (8 permutations).
# Contract (see data/instances.py): bash scripts/rankers/datashap.sh INSTANCES_DIR OUTPUT_DIR
# writes OUTPUT_DIR/<instance_id>.json = {"ranking": [...]} for every instance.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec python -m baseline.datashap_selection --instances "$1" --output-dir "$2"
