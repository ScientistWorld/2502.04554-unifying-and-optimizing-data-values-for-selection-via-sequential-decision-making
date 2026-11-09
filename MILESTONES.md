# Reproduction Milestones

**Current: core_claim**

## Progress Log

### [2026-11-09] - core_claim (hardening)
- Rebuilt the held-out test: secret-seeded instances generated inside `eval/test/`, every registered ranker run on their inputs, strict full-permutation validation, all metrics recomputed; closes the rebuilt-answers, larger-pool, seed cherry-pick, replaced-task and forged-output shortcuts.
- Replaced the non-reproducing `synthetic_planes` stand-in with the paper's `fried` dataset; the reproduced method now beats random, LOO and Data Shapley on both digits and fried on the held-out test (jobs `cc16bb60-089`, `553bd7c8-3f6`).
- Milestone stays `core_claim` (two of the paper's eight datasets; the theory/curvature and DP-gap experiments are not reproduced).

### [2026-06-02 04:10] - core_claim
- Final verification found an unverified structured-benchmark edit that did not have regenerated scores.
- Restored the verified binary structured tabular benchmark and kept the milestone at `core_claim`.
- No higher milestone is claimed because the additional structured setting remains weak.

### [2026-06-02 03:48] - core_claim
- Final verification completed.
- Regenerated stale scoring JSON files from existing curve artifacts so all declared metrics are present.
- Cleaned method-agnostic documentation wording and confirmed `python validate.py --compare` passes.

### [2026-06-02 03:45] - core_claim
- Audited the scoring contract and found `scores.json` was stale relative to the declared metrics.
- Patched the standard evaluator to emit all declared curve-quality and constraint metrics, restored 20-seed defaults, and updated the submitted job to regenerate scores from scratch.
- Keeping the current milestone at `core_claim` until the regeneration job validates in the container.

### [2026-06-02 03:18] - core_claim
- Job `3bd5ddd1-7cc` completed successfully and passed `python validate.py --compare`.
- The added Monte Carlo Data Shapley baseline ran on `digits_selection`; bipartite mean accuracy remained higher (`0.7967`) than DataShap (`0.7744`), random (`0.7475`), and LOO (`0.7218`).
- Restored `core_claim` after auditing and expanding the baseline coverage. The synthetic setting is still only marginal, so no higher milestone is claimed.

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
- Completed at milestone `core_claim`.
