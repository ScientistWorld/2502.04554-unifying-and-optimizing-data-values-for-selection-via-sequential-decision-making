# Audit protocol

Methods are constructed from the visible task/metric modules, baseline code,
and (for improve-mode checks) the reference method. No method reads hidden
curves, hidden scores, the paper, or the scoring reference. The audit's reporting
code reads reference coefficients only after all methods have run.

Each experiment's `run.sh` installs its persistent artifacts, exits the method
process, runs the visible train evaluator, then invokes the unmodified
`bash scripts/evaluate_test.sh` with **no arguments** in a new process. Nothing
depends on a surviving method process. No Python environment, evaluator module,
or metric implementation is changed. The task-replacement shortcut changes
only the visible `data/tasks.py` data provider. All outside files changed by
experiments are restored even on failure.

The three reference reruns hold dataset splits fixed and vary only the subset
sampling RNG. The original task seeds remain 1–20, with the evaluator deciding
the train/test slices. The stronger methods use only training/validation data.
The brute-force shortcut enumerates each available next candidate, rather than
all factorially many permutations, spending many more utility queries than the
reference. The oracle shortcut deliberately substitutes the reproducible test
labels for validation labels. Both are labelled shortcuts regardless of score.

Score comparisons use all nonzero coefficient magnitudes and experiment weights.
Since future-attempt variances do not exist yet, the report provides an explicit
audit-cohort normalization and every raw metric. No unique production rank can
be computed without the population of future attempts.
