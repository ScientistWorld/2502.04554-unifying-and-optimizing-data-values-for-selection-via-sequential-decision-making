# Overview

- **Paper ID:** 2502.04554
- **Title:** Unifying and Optimizing Data Values for Selection via Sequential-Decision-Making
- **Domain:** Data valuation / data selection / machine learning evaluation
- **TL;DR:** The paper reframes ranking-based data selection as a sequential optimization problem and proposes a practical utility surrogate for selecting small, high-value training subsets.

## Short Summary

The paper studies data valuation when the downstream use is selecting training examples under different subset budgets. It argues that a good ranking should perform well across the full selection curve, not just assign plausible standalone importance scores. The authors formalize this as a sequential decision problem whose cumulative reward is the sum of utilities over growing selected prefixes. They then connect existing game-theoretic data values to approximate dynamic programming and introduce a bipartite coverage surrogate to make the selection objective tractable at useful dataset sizes.

## Key Results

- Exact dynamic programming on small training sets exposes a noticeable gap between common data valuation rankings and the optimal sequential selection policy, especially at early budgets.
- Across eight OpenML-style datasets, the paper reports that the proposed practical selector improves mean test accuracy over Random, LOO, Influence, Data Shapley, Beta Shapley, Data Banzhaf, AME, DVRL, and Data-OOB in the main scaled experiment.
- Controlled curvature experiments support the claim that game-theoretic data values degrade as data points become more substitutable.

---

# Problem Definition

Given a pool of candidate training examples, a validation set used to estimate utility, and a fixed downstream learner, produce an ordering of the training examples for data selection. The ordering is evaluated by taking prefixes of increasing size, retraining the downstream learner on each prefix, and measuring held-out test performance.

This problem is method-agnostic: a valid solution may use any scoring, ranking, or selection strategy, as long as it outputs a single ordered list of the available training examples and uses only the allowed training/validation information.

## Research Question

Can a data selection method find a ranking whose prefixes achieve high downstream performance across many subset sizes, with particular emphasis on strong early-prefix performance when only a small number of examples can be selected?

## Why It Matters

Data selection is used when labeling, training, storage, or evaluation budgets are limited. A strong selector should identify useful data early and remain effective as the selected subset grows, rather than only optimizing a single fixed budget or producing importance scores that do not translate into good prefix performance.

## Tasks

Each task is a family of independent *instances* (random splits). An instance gives the method:

- a candidate training pool (features and labels), and
- a validation set (features and labels) for estimating utility,

plus an integer seed for the method's own randomness. Test data is never given to the method.

| Task | Data | Candidate pool | Validation | Test (hidden) |
|---|---|---:|---:|---:|
| `digits` | scikit-learn 8x8 handwritten digits, 10 classes | 100 | 100 | 1000 |
| `fried` | binarized Friedman #1 benchmark (OpenML "fried"), 10 features, 2 classes | 50 | 50 | 500 |

Features are standardized per instance. The downstream learner is scikit-learn logistic regression (`C=1.0`, `lbfgs`, `max_iter=500`).

## Interface

A method is a *ranker*: an executable script `scripts/rankers/<name>.sh` called as

```bash
bash scripts/rankers/<name>.sh INSTANCES_DIR OUTPUT_DIR
```

For every `INSTANCES_DIR/<instance_id>.npz` (arrays `x_train`, `y_train`, `x_valid`, `y_valid`; scalars `dataset`, `instance_id`, `seed`) it must write `OUTPUT_DIR/<instance_id>.json` containing `{"ranking": [...]}`, a permutation of `0..n-1` over the candidate pool. `data/instances.py` has readers/writers, and `python -m data.instances DIR` writes the visible development instances (seeds 1-20 per task; any other seed is available for development too).

## Success Criteria

A successful solution should:

- Improve the area under the test-performance selection curve across tasks.
- Reach competitive test accuracy with fewer selected examples, without giving up accuracy at larger budgets.
- Hold fixed the downstream learner, the instance inputs, the candidate pool and the evaluation protocol.
- Avoid using test labels, external data, or held-out evaluation code to construct the ranking.

---

# Paper's Method

## Key Contribution

The paper's main contribution is a unified sequential framework for data values used in selection. It shows that a ranking of training examples can be interpreted as a policy in a deterministic finite-horizon selection problem, where each state is the set of already selected examples and the objective is cumulative utility across all prefix sizes.

The paper then proposes a practical approximation based on a learned bipartite surrogate between training and validation examples. This surrogate is used to produce a selection order without exhaustively evaluating every possible training subset.

## Approach

The framework starts from the observation that ranking-based data values implicitly solve all prefix-budget selection problems at once. For a dataset `D` and utility function `U(S)`, the target objective is the average, equivalently the sum, of utilities over nested selected prefixes:

```text
maximize over permutations pi: sum_k U({pi(1), ..., pi(k)})
```

The exact formulation treats selected subsets as states, unselected training examples as actions, and subset utility as the reward signal. Backward dynamic programming computes the optimal value function and policy, then a forward pass converts the optimal trajectory into data values by assigning higher value to earlier selections. This exact solution is only feasible for small training pools because it requires utilities over exponentially many subsets.

The paper uses this formulation to reinterpret existing semi-value methods. Data Shapley, Beta Shapley, and Data Banzhaf can be viewed as approximate dynamic programming solutions that fit a linear utility surrogate and then act myopically by selecting the item with the largest fitted coefficient. This explains why these methods are optimal for linear utilities but can degrade when utility has high curvature and strong substitutability.

For the scalable method, the paper learns a bipartite graph between training examples and validation examples. Edges encode which validation examples a training example covers, using feature distance and matching labels with an adaptive threshold selected from sampled subset utilities. The resulting coverage utility is monotone submodular. The final selection is an iterative maximum-coverage process: repeatedly select the training example covering the most currently uncovered validation examples, remove the selected example and newly covered validation examples from consideration, and assign higher data values to earlier selected examples.

## Main Claims

- **Primary claim:** Optimizing data values for the sequential selection objective produces better selection curves than standard data valuation methods, especially for early prefixes.
- **Primary practical claim:** The bipartite surrogate closes much of the gap between tractable valuation methods and the optimal sequential policy while remaining computationally practical.
- **Secondary theoretical claim:** Existing semi-value methods are equivalent to myopic linear approximate dynamic programming policies for the sequential selection problem.
- **Secondary theoretical claim:** Under monotone submodular utility with curvature `c`, semi-value rankings have a `(1 - c)^2` approximation guarantee, explaining their degradation as substitutability increases.

---

# Evaluation

Evaluation measures how well a selection method orders a fixed candidate pool. For every instance, the evaluator takes each prefix of the submitted ordering, trains the fixed downstream learner on it, and records accuracy on that instance's test set. This file describes the measurement only; it does not constrain how the ordering is produced.

## How a method is scored

1. The evaluator builds the instances itself and writes only their method inputs (candidate pool + validation set + seed).
2. It runs every ranker found in `scripts/rankers/*.sh` on those inputs (contract in `briefing/problem.md`).
3. Each output must be exactly one ranking per instance and a permutation of that instance's full candidate pool, given as JSON integers. A missing, partial, duplicated, out-of-range, non-integer or otherwise malformed ranking, or a ranker that exits with an error, fails the whole evaluation: no scores are written.
4. The evaluator retrains logistic regression on prefixes `k = 1..n` and computes every metric itself from the resulting test accuracies. Nothing else a ranker writes is read.

Two slices use the same interface and the same instance distribution:

- **Visible slice** (`scripts/evaluate_train.sh`, `scripts/evaluate.sh`): seeds 1-20 of each task, built with `data/tasks.py` -> `scoring/scores_train.json` / `scoring/scores.json`.
- **Held-out slice** (`scripts/evaluate_test.sh`, no arguments): 100 instances per task drawn by the held-out evaluator from the same generators with seeds that are not available to methods -> `scoring/scores_test.json`. Methods never see these instances' inputs before evaluation, nor their test data at all.

## Metrics (per task, averaged over instances)

| Metric | Direction | Coefficient | Meaning |
|---|---|---:|---|
| `mean_accuracy` | higher | 1.0 | Mean test accuracy over the whole selection curve (prefix sizes `1..n`). |
| `early10_accuracy` | higher | 0.5 | Mean test accuracy over prefix sizes 1-10. |
| `early20_accuracy` | higher | 0.6 | Mean test accuracy over prefix sizes 1-20. |
| `tail_accuracy` | higher | 0.4 | Mean test accuracy over prefix sizes 21-`n`: early gains must not come at the cost of larger budgets. |
| `max_accuracy_drop` | lower | 0.2 | Largest one-step decrease of test accuracy along the curve. |
| `curve_accuracy_std` | lower | 0 (unscored) | Spread of test accuracy pooled over prefix sizes and instances (reported for comparison with the original study's +/-). |

Task weights: `digits_selection` 0.6, `fried_selection` 0.4. Coefficients and weights live in `scoring/reference.json`.

## Baselines

Implemented and scored through the same interface: random order (`random`), leave-one-out values (`loo`), and Monte Carlo Data Shapley with 8 permutations (`datashap`). The original study also compares Influence Function, Beta Shapley, Data Banzhaf, AME, DVRL and Data-OOB; their reported numbers are listed in `scoring/reference.json`.

## Reported targets from the original study

Mean test accuracy over the selection curve, 20 runs, logistic regression, pool size 50 (100 for digits and bbc-embed):

- 2dplanes 0.745, nomao 0.852, bbc-embed 0.878, MiniBooNE 0.754, **digits 0.764**, election 0.601, electricity 0.669, **fried 0.741**

Only digits and fried are part of this benchmark. Their absolute levels here differ from the study's because of preprocessing (class-balanced candidate pools, standardized features); compare methods with each other under this benchmark's protocol.

---

# Reproduction Log

### Iteration 1: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 24m | **GPU**: 0.0h
- **Jobs**: 5 total (2 completed, 3 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 01:30] - none
- Read the paper and identified the central method: sequential data selection with a learned bipartite coverage surrogate and greedy maximum coverage ranking.
- Implemented the first version of the method, random/LOO baselines, and a method-agnostic evaluator.
- Prepared a CPU job to run the end-to-end reproduction before claiming `method_runs`.

### [2026-06-02 01:46] - none
- Reviewed failed job `1097f20d-3d2`.
- Fixed scikit-learn 1.8 compatibility in the logistic regression evaluation helper.
- Resubmitting the same CPU reproduction job; no milestone claimed until the job completes successfully.

### [2026-06-02 01:51] - none
- Reviewed failed job `2acc7c12-ddc`.
- Fixed the target logistic regression solver for multiclass compatibility under scikit-learn 1.8.
- Resubmitting without claiming progress beyond `none`.

### [2026-06-02 01:58] - method_runs
- Job `a461534d-087` ran the paper's bipartite threshold-learning and greedy maximum-coverage selection method for all configured seeds and datasets.
- The job wrote ranking artifacts and `scoring/scores.json`; it failed only because `num_runs` was emitted as an undeclared metric.
- Digits results support the core effect direction, but the milestone remains `method_runs` until the official validation pass completes after the scoring-contract fix.

### [2026-06-02 02:12] - core_claim
- Job `5acc95ba-aa2` completed successfully and `validate.py --compare` passed.
- On `digits_selection`, the bipartite method outperformed both baselines with the same selection budget: mean accuracy `0.8006` versus random `0.7424` and LOO `0.7321`.
- Early-prefix behavior also supports the paper's claim: early20 accuracy `0.5970` versus random `0.4095` and LOO `0.3910`.
- The structured synthetic setting remains a failed additional setting and is not used to claim `core_claim_plus`.

### [2026-06-02 02:42] - core_claim
- Job `19c5bc2c-050` completed the same packaged reproduction with 20 seeds and passed `validate.py --compare`.
- The 20-seed digits result remains positive: bipartite mean accuracy `0.7967` versus random `0.7475` and LOO `0.7218`, with early20 accuracy `0.5997` versus random `0.4345` and LOO `0.3606`.
- The synthetic substitute shows only a very small mean advantage over LOO (`0.5710` versus `0.5704`), so it is documented as additional evidence but not strong enough for `core_claim_plus`.

</details>

### Iteration 2: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 6m | **GPU**: 0.0h
- **Jobs**: 5 total (2 completed, 3 failed)

<details>
<summary>Progress Log</summary>

### [2026-06-02 02:40] - core_claim
- Continuation audit completed from the reset `method_runs` state.
- Verified that `method/bipartite_selection.py` implements the paper's actual bipartite surrogate workflow: sampled subset utilities, feature/label thresholded train-validation graph learning, and greedy maximum uncovered-validation coverage ranking.
- Verified that evaluation is method-independent: `eval/evaluate_rankings.py` reads ranking artifacts, reconstructs the fixed task split, trains the fixed logistic-regression learner on ranking prefixes, and writes `scoring/scores.json`.
- Re-ran `python validate.py --compare`; scoring and separation checks passed.
- Attempted to acquire the actual OpenML 2dplanes dataset for a higher milestone, but OpenML metadata/download endpoints hung from this node. No fragile unverified URL was added.

### [2026-06-02 02:55] - core_claim
- Validated the reusable benchmark with `python validate.py --compare`.
- The implemented bipartite graph threshold-learning plus greedy maximum-coverage selector reproduces the core practical claim on the digits setting over 20 seeds.
- Reproduced digits mean selection accuracy: bipartite `0.7967`, LOO `0.7218`, random `0.7475`; early20 accuracy: bipartite `0.5997`, LOO `0.3606`, random `0.4345`.
- A second structured synthetic setting runs end-to-end but only shows a weak bipartite advantage over LOO, so the claimed milestone remains `core_claim` rather than `core_claim_plus`.

### [2026-06-02 02:35] - method_runs
- Implemented the paper's bipartite surrogate data-selection method and baseline rankings.
- Ran method, baselines, and method-agnostic evaluation end-to-end inside the packaged scripts.

</details>

### Iteration 3: gpt-5.5
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h
- **Jobs**: 6 total (3 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 4: gpt-5.5 (designer_stage_1)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 6 total (3 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 5: gpt-5.5 (designer_stage_2)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 6 total (3 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 6: gpt-5.5 (designer_stage_3)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 8 total (5 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 7: gpt-5.5 (packager)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 3m | **GPU**: 0.0h
- **Jobs**: 8 total (5 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 8: gpt-5.5 (verifier)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 6m | **GPU**: 0.0h
- **Jobs**: 8 total (5 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 9: gpt-5.5 (verifier)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 7m | **GPU**: 0.0h
- **Jobs**: 8 total (5 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 10: gpt-6.1-sol (redteam)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 9m | **GPU**: 0.0h
- **Jobs**: 9 total (6 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>

### Iteration 11: claude-opus-5-5 (hardener)
- **Milestone**: `core_claim` | **Status**: done
- **Working time**: 28m | **GPU**: 0.0h
- **Jobs**: 12 total (8 completed, 3 failed)

<details>
<summary>Progress Log</summary>

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

</details>


---

# Reproduction Milestones

**Current: core_claim**

## Stop Justification
- Completed at milestone `core_claim`.
