# Evaluation

Evaluation measures how well a selection method orders a fixed candidate pool. For every instance, the evaluator takes each prefix of the submitted ordering, trains the fixed downstream learner on it, and records accuracy on that instance's test set. This file describes the measurement only; it does not constrain how the ordering is produced.

## How a method is scored

1. The evaluator builds the instances itself and writes only their method inputs (candidate pool + validation set + seed).
2. It runs every ranker found in `scripts/rankers/*.sh` on those inputs (contract in `briefing/problem.md`).
3. Each output must be exactly one ranking per instance and a permutation of that instance's full candidate pool, given as JSON integers. A missing, partial, duplicated, out-of-range, non-integer or otherwise malformed ranking, or a ranker that exits with an error, fails the whole evaluation: no scores are written.
4. The evaluator retrains logistic regression on prefixes `k = 1..n` and computes every metric itself from the resulting test accuracies. Nothing else a ranker writes is read.

Two slices use the same interface and the same instance distribution:

- **Visible slice** (`scripts/evaluate_train.sh`, `scripts/evaluate.sh`): seeds 1-20 of each task, built with `data/tasks.py` -> `scoring/scores_train.json` / `scoring/scores.json`.
- **Held-out slice** (`scripts/evaluate_test.sh`, no arguments): 100 instances per task drawn by the held-out evaluator from the same generators with seeds that are not available to methods -> `scoring/scores_test.json`. Methods never see these instances' inputs before evaluation, nor their test data at all.

## Metrics (per task, averaged over instances)

| Metric | Direction | Coefficient | Meaning |
|---|---|---:|---|
| `mean_accuracy` | higher | 1.0 | Mean test accuracy over the whole selection curve (prefix sizes `1..n`). |
| `early10_accuracy` | higher | 0.5 | Mean test accuracy over prefix sizes 1-10. |
| `early20_accuracy` | higher | 0.6 | Mean test accuracy over prefix sizes 1-20. |
| `tail_accuracy` | higher | 0.4 | Mean test accuracy over prefix sizes 21-`n`: early gains must not come at the cost of larger budgets. |
| `max_accuracy_drop` | lower | 0.2 | Largest one-step decrease of test accuracy along the curve. |
| `curve_accuracy_std` | lower | 0 (unscored) | Spread of test accuracy pooled over prefix sizes and instances (reported for comparison with the original study's +/-). |

Task weights: `digits_selection` 0.6, `fried_selection` 0.4. Coefficients and weights live in `scoring/reference.json`.

## Baselines

Implemented and scored through the same interface: random order (`random`), leave-one-out values (`loo`), and Monte Carlo Data Shapley with 8 permutations (`datashap`). The original study also compares Influence Function, Beta Shapley, Data Banzhaf, AME, DVRL and Data-OOB; their reported numbers are listed in `scoring/reference.json`.

## Reported targets from the original study

Mean test accuracy over the selection curve, 20 runs, logistic regression, pool size 50 (100 for digits and bbc-embed):

- 2dplanes 0.745, nomao 0.852, bbc-embed 0.878, MiniBooNE 0.754, **digits 0.764**, election 0.601, electricity 0.669, **fried 0.741**

Only digits and fried are part of this benchmark. Their absolute levels here differ from the study's because of preprocessing (class-balanced candidate pools, standardized features); compare methods with each other under this benchmark's protocol.
