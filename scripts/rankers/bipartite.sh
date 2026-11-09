#!/bin/bash
# Ranker: The paper's bipartite-surrogate selector (reference method).
# Contract (see data/instances.py): bash scripts/rankers/bipartite.sh INSTANCES_DIR OUTPUT_DIR
# writes OUTPUT_DIR/<instance_id>.json = {"ranking": [...]} for every instance.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
exec python -m method.bipartite_selection --instances "$1" --output-dir "$2"
