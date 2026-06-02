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
