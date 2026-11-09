# Scientist Constraints

These constraints define what a future scientist must hold fixed when trying to improve the benchmark scores. The goal is to measure better data-selection methodology, not gains from changing the task, spending far more resources, or seeing the answers.

## Interface

Every method is a ranker in `scripts/rankers/<name>.sh` following the contract in `data/instances.py`: read instance files, write one `{"ranking": [...]}` per instance. The held-out evaluator runs every ranker in that directory on instances it builds itself. A ranker must rank each instance from that instance's inputs; it must not depend on files written by earlier evaluations.

## Target Learner

The downstream model is the benchmark's scikit-learn logistic regression (`C=1.0`, `lbfgs`, `max_iter=500`) on the provided standardized features. The evaluator owns it; a submitted ordering cannot change it.

## Data and Splits

Use only the two benchmark tasks, `digits` and `fried`, through the instance inputs. Do not bring in external labelled or unlabelled data. In particular, do not load another copy of the digits dataset or generate additional Friedman data inside a ranker to act as a larger validation or proxy test set: the held-out instances are drawn from these same public sources, so doing so leaks the test distribution. Do not read, import, copy or inspect `eval/test/` or any held-out scores, curves or temporary files from a ranker.

## Ranking Inputs

The ranking may use the candidate pool and the validation set of the instance (features and labels) and the instance seed. It must not use test data, test predictions or test-set feedback.

## Candidate Pool Size

The candidate pool is fixed by the instance: 100 points for `digits`, 50 for `fried`; validation 100 / 50; test 1000 / 500. A ranking must be a permutation of exactly the given pool (the evaluator rejects anything else).

## Utility-Evaluation Budget

At most 1000 target-model retrainings (or other subset-utility evaluations on the validation set) per instance to construct a ranking, as in the original study's experimental control. Exhaustive or near-exhaustive search, such as evaluating every remaining candidate at every step (5,050 retrainings for a 100-point pool), exceeds this budget. The evaluator cannot count retrainings, so this rule is checked in review.

## Instances and Repeats

The held-out evaluator fixes the instances (100 per task) and requires a ranking for every one of them. Rankers must be deterministic given the instance seed.

## Compliance Checklist

- [ ] The method is a ranker in `scripts/rankers/` that reads only the instance inputs.
- [ ] Target learner, features and splits are those given by the instance.
- [ ] No external data, no extra copies of the benchmark datasets, no regeneration of the generators.
- [ ] Nothing from `eval/test/` or from held-out outputs is read.
- [ ] Each ranking is a permutation of the full candidate pool.
- [ ] At most 1000 utility evaluations per instance.
