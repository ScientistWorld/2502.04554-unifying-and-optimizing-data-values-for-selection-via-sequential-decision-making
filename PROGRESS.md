# Progress

## What Works

- Paper analysis completed for the core RQ3 experiment.
- Implemented Algorithm 2's feature/label bipartite graph threshold learning and iterative maximum coverage ranking.
- Implemented random and leave-one-out baselines.
- Implemented method-agnostic evaluation that reads ranking artifacts and retrains logistic regression along the selection curve.
- Job `a461534d-087` ran the method and baselines end-to-end and produced ranking artifacts plus score files.

## Results

- Paper reference targets included for `digits_selection` and a structured tabular task analogous to `2dplanes`.
- Job `a461534d-087` reproduced the central effect on digits: bipartite mean accuracy `0.8006` versus LOO `0.7321` and random `0.7424`; early20 accuracy `0.5970` versus LOO `0.3910` and random `0.4095`.
- The same run did not show an advantage on `synthetic_planes_selection`: bipartite mean accuracy `0.5614` versus LOO `0.5677` and random `0.5659`.

## Remaining

- Rerun evaluation after removing the undeclared `num_runs` metric so validation passes.
- If validation succeeds, decide whether to claim `core_claim` on digits or improve the synthetic task before expanding.
- Expand to more seeds or additional OpenML datasets if budget allows.

## Issues

- Exact OpenML datasets are not downloaded yet. The first run uses bundled/generated data to avoid blocking the initial method execution.
- Job `1097f20d-3d2` failed before method execution because scikit-learn 1.8 removed the `multi_class` argument from `LogisticRegression`. Fixed in `data/metrics.py`.
- Job `2acc7c12-ddc` then failed because `liblinear` no longer supports multiclass without the removed `multi_class` option. Switched the target model helper to the multiclass-capable `lbfgs` solver.
- Job `a461534d-087` failed at `validate.py --compare` because `eval/evaluate_rankings.py` emitted `num_runs`, an undeclared metric. Removed `num_runs` from the score output.

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
- Experimental scale: the paper averages 20 runs. The first job runs five seeds to establish `method_runs` and, if results are positive, a minimal `core_claim`; later runs can increase to 20 seeds.
