# Progress

## What Works

- Paper analysis completed for the core RQ3 experiment.
- Implemented Algorithm 2's feature/label bipartite graph threshold learning and iterative maximum coverage ranking.
- Implemented random and leave-one-out baselines.
- Implemented method-agnostic evaluation that reads ranking artifacts and retrains logistic regression along the selection curve.
- Job `a461534d-087` ran the method and baselines end-to-end and produced ranking artifacts plus score files.
- Job `5acc95ba-aa2` completed the full reproduction script and passed `validate.py --compare`.

## Results

- Paper reference targets included for `digits_selection` and a structured tabular task analogous to `2dplanes`.
- Jobs `a461534d-087` and `5acc95ba-aa2` reproduced the central effect on digits: bipartite mean accuracy `0.8006` versus LOO `0.7321` and random `0.7424`; early20 accuracy `0.5970` versus LOO `0.3910` and random `0.4095`.
- The same run did not show an advantage on `synthetic_planes_selection`: bipartite mean accuracy `0.5614` versus LOO `0.5677` and random `0.5659`.

## Remaining

- Expand the successful digits reproduction to the paper's 20-run averaging protocol.
- Improve or replace the synthetic substitute before using it for `core_claim_plus`.
- Add accessible OpenML datasets if budget allows.

## Issues

- Exact OpenML datasets are not downloaded yet. The first run uses bundled/generated data to avoid blocking the initial method execution.
- Job `1097f20d-3d2` failed before method execution because scikit-learn 1.8 removed the `multi_class` argument from `LogisticRegression`. Fixed in `data/metrics.py`.
- Job `2acc7c12-ddc` then failed because `liblinear` no longer supports multiclass without the removed `multi_class` option. Switched the target model helper to the multiclass-capable `lbfgs` solver.
- Job `a461534d-087` failed at `validate.py --compare` because `eval/evaluate_rankings.py` emitted `num_runs`, an undeclared metric. Removed `num_runs` from the score output.
- Job `5acc95ba-aa2` passed, confirming the scoring-contract fix.

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
- Experimental scale: the paper averages 20 runs. The first validated reproduction used five seeds to establish `core_claim`; the next submitted job expands to 20 seeds.
