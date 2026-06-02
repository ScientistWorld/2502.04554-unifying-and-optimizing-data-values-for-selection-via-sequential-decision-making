# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-06-02 02:55] - core_claim
- Validated the reusable benchmark with `python validate.py --compare`.
- The implemented bipartite graph threshold-learning plus greedy maximum-coverage selector reproduces the core practical claim on the digits setting over 20 seeds.
- Reproduced digits mean selection accuracy: bipartite `0.7967`, LOO `0.7218`, random `0.7475`; early20 accuracy: bipartite `0.5997`, LOO `0.3606`, random `0.4345`.
- A second structured synthetic setting runs end-to-end but only shows a weak bipartite advantage over LOO, so the claimed milestone remains `core_claim` rather than `core_claim_plus`.

### [2026-06-02 02:35] - method_runs
- Implemented the paper's bipartite surrogate data-selection method and baseline rankings.
- Ran method, baselines, and method-agnostic evaluation end-to-end inside the packaged scripts.

## Stop Justification
- Completed at milestone `core_claim`: the paper's actual practical algorithm runs end-to-end and the minimum experiment supports the central claim.
