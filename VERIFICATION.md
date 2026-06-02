# Verification Report

## Initial Assessment

The workspace started from a claimed `core_claim` milestone with a faithful implementation of the paper's bipartite data-selection algorithm, reusable ranking artifacts, and working aggregate scores. The core digits result justified `core_claim`: the proposed selector outperformed random, leave-one-out, and Monte Carlo Data Shapley baselines on the packaged sequential-selection protocol.

## Issues Found

- **Critical, fixed:** A later unverified edit changed the structured synthetic benchmark to a multiclass task and added Data Shapley to that setting, but `scoring/scores.json`, `scores_train.json`, and `scores_test.json` still contained results from the earlier verified binary task without the synthetic Data Shapley method. This made the code/docs inconsistent with recorded scores.
- **Minor, accepted:** The structured synthetic setting remains weakly positive and is not enough to support a higher milestone. The core claim rests on the stronger digits experiment.
- **Minor, accepted:** The exact OpenML datasets from the paper were not fetched because candidate OpenML URLs/API calls could not be verified from the login node. The workspace documents the self-contained data substitution.
- **Cosmetic, not modified:** Pre-existing system-level git dirt remains in `README.md`, `manifest.json`, and deleted `trajectory/*.jsonl` files. These appear unrelated to the research environment and were left untouched.

## Fixes Applied

- Restored `data/tasks.py` to the verified binary structured synthetic benchmark that matches existing ranking and score artifacts.
- Restored `scripts/reproduce.sh` so the packaged reproduction runs Data Shapley only for the verified digits setting.
- Updated `scoring/reference.json`, `scoring/TARGETS.md`, `scoring/EXPERIMENTS.md`, `PROGRESS.md`, and `MILESTONES.md` to describe the verified benchmark rather than the unrun multiclass extension.
- Set `action.yaml` to `action: done` with milestone `core_claim`.
- Re-ran lightweight validation: scoring schema comparison, shell syntax checks, method/eval separation scans, and Python bytecode compilation for core modules.

## Final Judgment

The workspace is ready to serve as a research gym at `core_claim`. Improve-mode agents can build on the implemented method and baselines; from-scratch agents can use the method-agnostic problem, data, and evaluation interface without importing the paper method. The main limitation is data coverage: the gym uses bundled/generated substitutes rather than the full OpenML suite, and only the digits experiment provides a strong reproduced advantage.

- Milestone: core_claim
- Ready for gym use: yes
- Confidence: medium
- Key limitation: self-contained substitute data, with the strongest reproduced claim on digits only
