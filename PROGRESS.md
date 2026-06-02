# Progress

## What Works

- Paper analysis completed for the core RQ3 experiment.
- Implemented Algorithm 2's feature/label bipartite graph threshold learning and iterative maximum coverage ranking.
- Implemented random and leave-one-out baselines.
- Implemented method-agnostic evaluation that reads ranking artifacts and retrains logistic regression along the selection curve.

## Results

- No completed compute-node results yet. The next submitted job will write `scoring/scores.json`.
- Paper reference targets included for `digits_selection` and a structured tabular task analogous to `2dplanes`.

## Remaining

- Run the end-to-end pipeline on a compute node.
- Inspect whether bipartite outperforms random and LOO on at least one non-trivial task.
- If the first run supports the core claim, expand to more seeds or additional OpenML datasets.

## Issues

- Exact OpenML datasets are not downloaded yet. The first run uses bundled/generated data to avoid blocking the initial method execution.
- Job `1097f20d-3d2` failed before method execution because scikit-learn 1.8 removed the `multi_class` argument from `LogisticRegression`. Fixed in `data/metrics.py`.
- Job `2acc7c12-ddc` then failed because `liblinear` no longer supports multiclass without the removed `multi_class` option. Switched the target model helper to the multiclass-capable `lbfgs` solver.

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
