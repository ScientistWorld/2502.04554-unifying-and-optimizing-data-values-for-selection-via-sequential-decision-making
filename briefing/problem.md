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
