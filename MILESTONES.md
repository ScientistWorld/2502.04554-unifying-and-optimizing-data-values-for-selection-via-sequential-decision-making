# Reproduction Milestones

**Current: none**

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

## Stop Justification
- Not stopped.
