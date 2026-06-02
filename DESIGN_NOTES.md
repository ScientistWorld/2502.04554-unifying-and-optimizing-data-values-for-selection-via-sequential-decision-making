# Design Notes

## Checks Performed

- Read `eval/train/evaluate.py`, `eval/test/evaluate.py`, `eval/evaluate_rankings.py`, and both train/test shell wrappers side by side.
- Confirmed the split is seed-based: train uses seeds 1-10 and test uses seeds 11-20.
- Confirmed evaluators read method-produced ranking artifacts from `checkpoints/rankings` rather than importing or rerunning `method/`.
- Confirmed `scripts/evaluate_test.sh` calls `eval.test.evaluate`, writes `scoring/scores_test.json`, and emits test-marked curve artifacts.
- Grepped for train/test cross-imports and did not find leakage between `eval/train/` and `eval/test/`.
- Grepped for paper-agreement metric names and found no forbidden metric entries; remaining "paper" references are descriptive experiment text.
- Confirmed `scoring/scores_train.json` and `scoring/scores_test.json` do not exist.
- Ran `bash -n` on `scripts/evaluate_train.sh` and `scripts/evaluate_test.sh`.

## Changes Made

- Added train/test curve-shape metrics computed from the existing selection curves:
  - `early10_accuracy` for stricter low-budget sample-efficiency pressure.
  - `tail_accuracy` for sustained post-early performance.
  - `worst_prefix_accuracy` to expose fragile rankings that only optimize a few checkpoints.
  - `max_accuracy_drop` to penalize sharp regressions along the curve.
  - `early_label_coverage` to discourage early prefixes that exploit narrow class composition.
- Mirrored the metric implementation independently in `eval/train/evaluate.py` and `eval/test/evaluate.py` to avoid cross-slice imports.
- Updated `scoring/reference.json` so every metric with a nonzero coefficient has `higher_is_better`, `coefficient`, and `description`.
- Added reference entries and coefficients for the new metrics in both existing experiments.

## Runtime Concerns For Next Iteration

- I did not run Python evaluators or generate scores in this design-only iteration.
- `selection_budget` is still effectively constant because evaluators require full rankings; it remains a low-weight constraint but is not a strong anti-shortcut signal.
- The new `early_label_coverage` metric is intentionally small-weighted. It catches degenerate early class collapse, but it should not dominate actual curve accuracy.
- The held-out test evaluator expects methods present in `scores_train.json` to have corresponding held-out seed ranking artifacts. If a future run only produces train seeds, test evaluation should fail rather than silently score a different method set.
