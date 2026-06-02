# Progress

## What Works

- Paper analysis completed for the core RQ3 experiment.
- Implemented Algorithm 2's feature/label bipartite graph threshold learning and iterative maximum coverage ranking.
- Implemented random, leave-one-out, and Monte Carlo Data Shapley baselines.
- Implemented method-agnostic evaluation that reads ranking artifacts and retrains logistic regression along the selection curve.
- Job `a461534d-087` ran the method and baselines end-to-end and produced ranking artifacts plus score files.
- Job `5acc95ba-aa2` completed the full reproduction script and passed `validate.py --compare`.
- Job `19c5bc2c-050` expanded the packaged reproduction to 20 seeds and passed `validate.py --compare`.
- Job `3bd5ddd1-7cc` reran the packaged reproduction with the added Monte Carlo Data Shapley baseline and passed `validate.py --compare`.
- The current workspace passes `python validate.py --compare` and is complete at `core_claim`.
- Continuation audit confirmed the method and evaluation are real rather than surrogate or hardcoded: the method outputs rankings, and the evaluator independently scores those rankings.
- Current turn patched stale scoring-contract gaps: `scripts/evaluate.sh` now emits every metric declared in `reference.json`, split evaluators include `final_accuracy` and `selection_budget`, and reproduction defaults are back to 20 seeds.
- Final verification regenerated `scores.json`, `scores_train.json`, and `scores_test.json` from existing curve artifacts and confirmed the expanded scoring contract passes validation.

## Results

- Paper reference targets included for `digits_selection` and a structured tabular task analogous to `2dplanes`.
- Jobs `a461534d-087` and `5acc95ba-aa2` reproduced the central effect on digits: bipartite mean accuracy `0.8006` versus LOO `0.7321` and random `0.7424`; early20 accuracy `0.5970` versus LOO `0.3910` and random `0.4095`.
- The final 20-seed run preserved the central effect on digits: bipartite mean accuracy `0.7967` versus LOO `0.7218` and random `0.7475`; early20 accuracy `0.5997` versus LOO `0.3606` and random `0.4345`.
- The continuation run with Data Shapley preserved the central effect on digits: bipartite mean accuracy `0.7967` versus DataShap `0.7744`, random `0.7475`, and LOO `0.7218`; early20 accuracy `0.5997` versus DataShap `0.4860`, random `0.4345`, and LOO `0.3606`.
- The final 20-seed `synthetic_planes_selection` result is weakly positive but not strong enough for a higher milestone: bipartite mean accuracy `0.5710` versus LOO `0.5704` and random `0.5482`.
- Milestone claimed: `core_claim`, because the digits experiment demonstrates the paper's practical claim that the bipartite selector produces a better selection curve than standard baselines under the paper's RQ3 protocol.

## Remaining

- Higher milestones require adding more of the paper's OpenML datasets or improving the synthetic substitute so the additional setting has a clear, reproducible method advantage.
- A future agent can start from the packaged scripts and current 20-seed scores without needing to repair the environment.
- Higher milestones still require additional original OpenML-style datasets or a stronger nontrivial substitute setting.

## Issues

- Continuation audit noted that the previous core claim relied only on random and LOO baselines; this was fixed by adding and validating a Monte Carlo Data Shapley baseline on `digits_selection`.
- Exact OpenML datasets are not downloaded yet. The first run uses bundled/generated data to avoid blocking the initial method execution.
- A continuation attempt to fetch OpenML 2dplanes (dataset ID 727) via both `fetch_openml` and direct OpenML API/download URLs hung from the login node, so no unverified download URL was committed.
- Job `1097f20d-3d2` failed before method execution because scikit-learn 1.8 removed the `multi_class` argument from `LogisticRegression`. Fixed in `data/metrics.py`.
- Job `2acc7c12-ddc` then failed because `liblinear` no longer supports multiclass without the removed `multi_class` option. Switched the target model helper to the multiclass-capable `lbfgs` solver.
- Job `a461534d-087` failed at `validate.py --compare` because `eval/evaluate_rankings.py` emitted `num_runs`, an undeclared metric. Removed `num_runs` from the score output.
- Job `5acc95ba-aa2` passed, confirming the scoring-contract fix.
- Job `19c5bc2c-050` passed after the 20-seed expansion.
- Job `3bd5ddd1-7cc` passed after the Data Shapley baseline expansion.
- The login-node Python environment lacks `numpy`, so the expanded evaluator was syntax-checked locally and will be executed in the submitted container, where `environment/setup.sh` installs the required packages.
- Because the per-seed curve artifacts already existed, final verification recomputed aggregate scoring JSON files without re-running training.

## Deviations from Paper

<!-- Do not edit this section unless you deviated from the paper's original setup.
     For each deviation, document: what the paper used, what you substituted, and why.

     ACCEPTABLE deviations (data/resource/scale substitutions — milestones still valid):
       - Replaced a proprietary dataset with a public one
       - Used a smaller model of the same architecture
       - Scaled down training (fewer epochs, smaller batch)
       - Used a different library for the same algorithm

     UNACCEPTABLE deviations (algorithm substitutions — milestones above 'none' are void):
       - Replaced the paper's algorithm with a fundamentally different one
       - Wrote a generic model trained to approximate the method's outputs
         instead of implementing the method's computational steps

- Data resource/scale: the paper evaluates eight OpenML datasets. The first runnable reproduction uses scikit-learn digits and a generated structured binary-classification dataset analogous to 2dplanes so no external data download is required before the first compute submission.
- Experimental scale: the paper averages 20 runs. The final validated reproduction uses 20 seeds for the packaged CPU benchmark.
