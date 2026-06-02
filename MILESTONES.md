# Reproduction Milestones

**Current: core_claim**

<!-- Milestone levels (update "Current" above as you progress):
  none             — just started, no meaningful progress yet
  method_runs      — the paper's method executes end-to-end without errors
  core_claim       — minimum experiment supports the paper's central claim
  core_claim_plus  — core claim reproduced on additional settings
  secondary_claims — secondary results or contributions reproduced
  majority         — more than half of reported results reproduced
  near_complete    — most results reproduced, only minor gaps remain
  full             — all reported results reproduced
-->

## Progress Log

### [2026-06-02 01:30] - none
- Read the paper and identified the central method: sequential data selection with a learned bipartite coverage surrogate and greedy maximum coverage ranking.
- Implemented the first version of the method, random/LOO baselines, and a method-agnostic evaluator.
- Prepared a CPU job to run the end-to-end reproduction before claiming `method_runs`.

### [2026-06-02 01:46] - none
- Reviewed failed job `1097f20d-3d2`.
- Fixed scikit-learn 1.8 compatibility in the logistic regression evaluation helper.
- Resubmitting the same CPU reproduction job; no milestone claimed until the job completes successfully.

### [2026-06-02 01:51] - none
- Reviewed failed job `2acc7c12-ddc`.
- Fixed the target logistic regression solver for multiclass compatibility under scikit-learn 1.8.
- Resubmitting without claiming progress beyond `none`.

### [2026-06-02 01:58] - method_runs
- Job `a461534d-087` ran the paper's bipartite threshold-learning and greedy maximum-coverage selection method for all configured seeds and datasets.
- The job wrote ranking artifacts and `scoring/scores.json`; it failed only because `num_runs` was emitted as an undeclared metric.
- Digits results support the core effect direction, but the milestone remains `method_runs` until the official validation pass completes after the scoring-contract fix.

### [2026-06-02 02:12] - core_claim
- Job `5acc95ba-aa2` completed successfully and `validate.py --compare` passed.
- On `digits_selection`, the bipartite method outperformed both baselines with the same selection budget: mean accuracy `0.8006` versus random `0.7424` and LOO `0.7321`.
- Early-prefix behavior also supports the paper's claim: early20 accuracy `0.5970` versus random `0.4095` and LOO `0.3910`.
- The structured synthetic setting remains a failed additional setting and is not used to claim `core_claim_plus`.

### [2026-06-02 02:42] - core_claim
- Job `19c5bc2c-050` completed the same packaged reproduction with 20 seeds and passed `validate.py --compare`.
- The 20-seed digits result remains positive: bipartite mean accuracy `0.7967` versus random `0.7475` and LOO `0.7218`, with early20 accuracy `0.5997` versus random `0.4345` and LOO `0.3606`.
- The synthetic substitute shows only a very small mean advantage over LOO (`0.5710` versus `0.5704`), so it is documented as additional evidence but not strong enough for `core_claim_plus`.

## Stop Justification
- Completed at milestone `core_claim`.
