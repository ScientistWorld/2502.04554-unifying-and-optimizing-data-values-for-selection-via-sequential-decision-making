# Evaluation

Evaluation measures how well a submitted data selection method orders a fixed training pool. The evaluator builds prefixes of the submitted ordering, trains the fixed downstream learner on each prefix, and records held-out test accuracy.

This file intentionally describes only the task, metrics, baselines, and fair-comparison rules. It does not constrain the internal method used to produce the ordering.

## Metrics

- **Mean selection accuracy:** mean test accuracy over the evaluated prefix budgets for a dataset and seed. Higher is better.
- **Selection AUC / cumulative utility:** area under the test accuracy versus selected-prefix-size curve, or the equivalent average over recorded prefix accuracies. Higher is better.
- **Early-prefix accuracy:** test accuracy at small selected budgets, such as the first 10-30 percent of the training pool. Higher is better.
- **Best-baseline gap:** difference between a submitted method and the strongest reference baseline under the same dataset, split, learner, and budget. Higher is better.
- **Utility-query budget:** number of downstream model retrainings or subset utility evaluations used to produce the ranking. Lower is better, subject to achieving the selection metrics.

## Baselines and Targets

The original study compares against Random, Leave-one-out, Influence Function, Data Shapley, Beta Shapley, Data Banzhaf, AME, DVRL, and Data-OOB. This gym includes the implemented baselines reported in `scoring/scores.json`; future methods should compare against them under the same splits and learner.

The original study reports these practical mean-accuracy targets across eight datasets:

- 2dplanes: 0.745 mean test accuracy
- nomao: 0.852 mean test accuracy
- bbc-embed: 0.878 mean test accuracy
- MiniBooNE: 0.754 mean test accuracy
- digits: 0.764 mean test accuracy
- election: 0.601 mean test accuracy
- electricity: 0.669 mean test accuracy
- fried: 0.741 mean test accuracy

These targets should be interpreted under the original study's stated protocol: mean test accuracy across 20 independent runs, with selection budgets of 50 points for standard datasets and 100 points for digits and bbc-embedding.

## Evaluation Protocol

Use the fixed benchmark data splits and downstream learner. The benchmark uses scikit-learn Logistic Regression as the target model whose test accuracy defines utility.

For each dataset and seed:

1. Provide a ranking of the candidate training examples.
2. For each evaluated prefix size `k`, train the target learner on the first `k` ranked examples.
3. Evaluate the trained learner on the held-out test set.
4. Aggregate accuracy over prefix sizes to produce the selection curve metrics.
5. Average results over the same 20 independent trials used by the benchmark.

The practical scaled comparison uses 50 training, 50 validation, and 500 test points for standard tabular datasets; digits-style multiclass tasks use 100 training, 100 validation, and 1000 test points. All methods should respect the same maximum model-retraining or utility-query budget used by the evaluation.
