#!/bin/bash
# Download all data and models needed for this environment.
#
# Estimated total download size: 0 GB (beyond the Python packages that
# environment/setup.sh installs).
#
# Nothing has to be fetched:
#   - digits: shipped inside the scikit-learn package
#     (sklearn.datasets.load_digits reads it from the installed package).
#   - fried (OpenML 901): regenerated from its published definition with
#     sklearn.datasets.make_friedman1 (Friedman #1, noise 1.0), binarized at
#     the mean as OpenML does.
# The check below fails loudly if scikit-learn is missing or incomplete.
set -e

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR/.."

mkdir -p data/downloads
python -c "from sklearn.datasets import load_digits, make_friedman1; d = load_digits(); make_friedman1(n_samples=10, random_state=0); print('digits available:', d.data.shape)"
