#!/bin/bash
# Job entry point: reproduce the reference end to end, then run the
# hardening checks (variants and shortcuts through the held-out evaluator),
# summarize them, and validate the workspace.
set -uo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

echo "== $(date -u +%FT%TZ) reproduce (visible + held-out)"
bash scripts/reproduce.sh || { echo "reproduce failed"; exit 1; }

echo "== $(date -u +%FT%TZ) hardening checks"
python -m redteam.hardening.harness

echo "== $(date -u +%FT%TZ) summarize"
python -m redteam.hardening.summarize

echo "== $(date -u +%FT%TZ) validate"
python validate.py --compare --post-design
echo "== $(date -u +%FT%TZ) done"
