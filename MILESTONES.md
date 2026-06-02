# Reproduction Milestones

**Current: method_runs**

## Progress Log

### [2026-06-02 03:08] - method_runs
- Continuation audit found the bipartite implementation is faithful, but baseline coverage was thin for a restored `core_claim`.
- Added a Monte Carlo Data Shapley baseline using random-permutation marginal utilities and wired it into the reproduction job for `digits_selection`.
- Submitting a CPU job to regenerate rankings, curves, and scores from scratch before restoring `core_claim`.

### [2026-06-02 02:43] - core_claim
- Implemented the paper's feature/label bipartite graph threshold learner and iterative maximum-coverage selector.
- Ran the packaged 20-seed reproduction job and validated `scoring/scores.json` with `python validate.py --compare`.
- Reproduced the central practical effect on `digits_selection`: bipartite mean accuracy `0.7967` versus LOO `0.7218` and random `0.7475`, with a stronger early-prefix gap.

### [2026-06-02 01:24] - method_runs
- Implemented random and leave-one-out baselines plus method-agnostic ranking evaluation.
- Confirmed the bipartite method and baselines execute end-to-end and produce ranking artifacts.

### [2026-06-02 01:11] - none
- Started reproduction work and read the paper's sequential data selection and bipartite surrogate sections.

## Stop Justification
- Not stopped. A new CPU job is being submitted to test the added Data Shapley baseline and regenerate scores.
