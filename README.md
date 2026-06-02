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

## Success Criteria

A successful solution should:

- Improve the area under the test-performance selection curve across datasets.
- Reach competitive test accuracy with fewer selected examples.
- Remain fair under the same downstream learner, train/validation/test splits, candidate pool sizes, random seeds, and retraining budget used by the benchmark.
- Avoid using test labels or external data to construct the ranking.

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

Evaluation measures how well a submitted data selection method orders a fixed training pool. The evaluator builds prefixes of the submitted ordering, trains the fixed downstream learner on each prefix, and records held-out test accuracy.

This file intentionally describes only the task, metrics, baselines, and fair-comparison rules. It does not constrain the internal method used to produce the ordering.

## Metrics

- **Mean selection accuracy:** mean test accuracy over the evaluated prefix budgets for a dataset and seed. Higher is better.
- **Selection AUC / cumulative utility:** area under the test accuracy versus selected-prefix-size curve, or the equivalent average over recorded prefix accuracies. Higher is better.
- **Early-prefix accuracy:** test accuracy at small selected budgets, such as the first 10-30 percent of the training pool or the paper's early checkpoints. Higher is better.
- **Best-baseline gap:** difference between a submitted method and the strongest non-oracle baseline under the same dataset, split, learner, and budget. Higher is better.
- **Oracle gap:** difference between the submitted method and the exact optimal sequential policy on small-pool experiments where exhaustive dynamic programming is feasible. Lower is better.
- **Runtime / utility-query budget:** wall-clock time, number of downstream model retrainings, or number of subset utility evaluations used to produce the ranking. Lower is better, subject to achieving the selection metrics.

## Baselines and Targets

The paper compares against Random, Leave-one-out, Influence Function, Data Shapley, Beta Shapley, Data Banzhaf, AME, DVRL, and Data-OOB. For small-pool optimality analysis, exact dynamic programming is an oracle reference rather than a practical baseline.

The main reported practical target is the paper's bipartite-selection performance across eight datasets:

- 2dplanes: 0.745 mean test accuracy
- nomao: 0.852 mean test accuracy
- bbc-embed: 0.878 mean test accuracy
- MiniBooNE: 0.754 mean test accuracy
- digits: 0.764 mean test accuracy
- election: 0.601 mean test accuracy
- electricity: 0.669 mean test accuracy
- fried: 0.741 mean test accuracy

These targets should be interpreted under the paper's stated protocol: mean test accuracy across 20 independent runs, with selection budgets of 50 points for standard datasets and 100 points for digits and bbc-embedding.

## Evaluation Protocol

Use the fixed benchmark data splits and downstream learner. The paper uses scikit-learn Logistic Regression as the target model whose test accuracy defines utility.

For each dataset and seed:

1. Provide a ranking of the candidate training examples.
2. For each evaluated prefix size `k`, train the target learner on the first `k` ranked examples.
3. Evaluate the trained learner on the held-out test set.
4. Aggregate accuracy over prefix sizes to produce the selection curve metrics.
5. Average results over the same 20 independent trials used by the benchmark.

The small-pool oracle comparison uses 20 training points, 100 validation points, and 500 test points per dataset, with seeds from 10 to 200 in steps of 10. The practical scaled comparison uses 50 training, 50 validation, and 500 test points for standard datasets; digits and bbc-embedding use 100 training, 100 validation, and 1000 test points. All non-oracle methods should respect the same maximum model-retraining budget used by the evaluation.

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


---

# Reproduction Milestones

**Current: core_claim**

## Stop Justification
- Completed at milestone `core_claim`.
