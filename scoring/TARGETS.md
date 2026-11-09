# Evaluation Targets

A method receives the instance inputs (candidate pool + validation set) and returns one ordering of the full candidate pool per instance. The evaluator retrains the fixed logistic-regression learner on every prefix and scores test accuracy. Held-out scores come from `scripts/evaluate_test.sh` over 100 hidden instances per task.

## Primary: digits_selection (weight 0.6)

Sequential selection on the handwritten-digits task (pool 100, validation 100, test 1000).

- **Benefit metrics (higher is better):** `mean_accuracy` (1.0), `early10_accuracy` (0.5), `early20_accuracy` (0.6)
- **Constraint metrics:** `tail_accuracy` (0.4, higher is better: larger-budget prefixes must stay good), `max_accuracy_drop` (0.2, lower is better: no regressions as data is added)
- **Hard constraints enforced by the evaluator (violations fail the run):** one ranking per held-out instance; each a permutation of that instance's whole candidate pool; rankers run only on the evaluator-provided inputs.
- **Reported, unscored:** `curve_accuracy_std`
- **Reference (reproduced, held-out):** see `scoring/scores_test.json` (`bipartite`); the original study reports 0.764 mean accuracy for its method and 0.680 for the best of its baselines on digits.

## Primary: fried_selection (weight 0.4)

Sequential selection on the binarized Friedman #1 ("fried") task (pool 50, validation 50, test 500).

- **Benefit metrics (higher is better):** `mean_accuracy` (1.0), `early10_accuracy` (0.5), `early20_accuracy` (0.6)
- **Constraint metrics:** `tail_accuracy` (0.4), `max_accuracy_drop` (0.2, lower is better)
- **Hard constraints:** as above.
- **Reported, unscored:** `curve_accuracy_std`
- **Reference (reproduced, held-out):** see `scoring/scores_test.json` (`bipartite`); the original study reports 0.741 for its method versus 0.702 random, 0.698 leave-one-out and 0.710 Data Shapley on fried.

## Rule-based constraint (checked by review, not measurable by the evaluator)

- At most 1000 target-model retrainings / subset-utility evaluations per instance to build a ranking (the original study's experimental control). See `scoring/CONSTRAINTS.md`.
