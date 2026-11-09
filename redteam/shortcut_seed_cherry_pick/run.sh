#!/bin/bash
set -euo pipefail
cd /home/user
if [ ! -f redteam/reference_seed0/rankings/bipartite_digits_seed1.json ]; then
  bash redteam/reference_seed0/run.sh
fi
python -m redteam.harness shortcut_seed_cherry_pick
