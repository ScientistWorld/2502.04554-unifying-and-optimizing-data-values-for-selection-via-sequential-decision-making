# Research Direction

## Research Problem

This benchmark is about ranking training examples for data selection. The central question is whether a method can produce a single ordering whose prefixes perform well across all selection budgets for a fixed downstream learner, with early budgets mattering most.

## Core Contribution Scope

A scientist should work on methods that improve data valuation or data ranking for prefix-based selection: how the ordering is produced, how validation utility is modelled, how dependencies and redundancy between examples are captured, or how selection quality across budgets is optimized under a limited number of utility evaluations.

## Approach Scope

In scope: new valuation functions, utility surrogates, subset-ranking objectives, sequential selection policies, diversity- or coverage-aware rules, better use of the validation set, and better ordering of the later (larger-budget) part of the ranking. The method may be deterministic or learned on the visible instances, exact or approximate, as long as it is a ranker that outputs a complete ordering of each instance's candidate pool within the utility-evaluation budget.

## Known Room for Improvement

The reproduced reference is far from the bound on every scored metric (mean accuracy about 0.80 on digits; early-prefix accuracy well below later-prefix accuracy). Simple variants that keep the reference's information budget, for example ordering the remainder of the pool more carefully once early selection has saturated, already score above it on the held-out slice.

## Out of Bounds

- Changing the task, the learner, the features or the candidate pool.
- Using external data, extra copies of the benchmark datasets, regenerated synthetic data, or any test-set or held-out-evaluator information.
- Exceeding 1000 utility evaluations per instance (e.g. trying every remaining candidate at every step).
- Ranking only part of the pool or returning anything other than a full permutation.
