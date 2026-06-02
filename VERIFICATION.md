# Verification Report

## Initial Assessment

The workspace entered final verification at milestone `core_claim`. The claimed milestone is justified: the paper's actual bipartite ranking procedure is implemented in `method/`, ranking artifacts exist, and the reproduced `digits_selection` result shows the proposed method ahead of Random, Leave-one-out, and Monte Carlo Data Shapley under the benchmark's selection-curve protocol.

## Issues Found

- **Minor:** `scoring/scores.json`, `scores_train.json`, and `scores_test.json` were stale relative to the expanded metric definitions. They were missing several declared curve-quality metrics even though existing per-seed curve artifacts contained enough information to recompute them.
- **Minor:** `briefing/evaluation.md` contained method-identifying wording for the original proposed selector, which was not appropriate for a strictly method-agnostic problem/evaluation briefing.
- **Minor:** `scoring/reference.json` declared auxiliary gym metrics that the original paper did not report, without notes explaining why reference result rows only contained the paper-reported mean/stability/budget fields.

## Fixes Applied

- Regenerated `scoring/scores.json`, `scoring/scores_train.json`, and `scoring/scores_test.json` from existing per-seed curve artifacts so every declared metric is present for each scored method and experiment.
- Reworded `briefing/evaluation.md`, `scoring/CONSTRAINTS.md`, `scoring/DIRECTION.md`, and one data helper docstring to keep from-scratch-facing files method-agnostic.
- Added `notes` fields to `scoring/reference.json` documenting that auxiliary gym metrics are computed by the evaluator but were not reported as paper reference values.
- Ran `python validate.py --compare`; all scoring and structural checks passed.
- Confirmed `scripts/download.sh` is self-contained and shared-free; no external downloads are required.

## Final Judgment

The workspace is ready to serve as a research gym at `core_claim`. Improve-mode agents can build on the implemented method and baselines, while from-scratch agents can use the method-agnostic problem, data, and evaluation pipeline without importing from `method/`.

- Milestone: core_claim
- Ready for gym use: yes
- Confidence: medium
- Key limitation: The strongest claim is demonstrated on `digits_selection`; the substitute `synthetic_planes_selection` remains weakly positive and is not enough for a higher milestone.
