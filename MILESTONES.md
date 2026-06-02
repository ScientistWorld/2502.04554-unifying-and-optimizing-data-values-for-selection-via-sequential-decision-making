# Reproduction Milestones

**Current: core_claim**

## Progress Log

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
- Completed at milestone `core_claim`. Higher milestones would require adding more of the paper's OpenML datasets or designing a stronger second substitute task; the current environment is packaged and validated for the core claim.
