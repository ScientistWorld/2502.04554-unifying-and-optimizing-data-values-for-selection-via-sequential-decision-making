# Scientist Constraints

These constraints define what a future scientist must hold fixed when trying to improve the benchmark scores. The goal is to measure better data selection methodology, not gains from changing the learning task or spending more resources.

## Target Learner

The downstream model used to evaluate selected prefixes must remain the benchmark's scikit-learn Logistic Regression target learner. The paper's claim is about selecting data for a fixed learner; switching to a stronger classifier, neural network, ensemble, or tuned model would improve test accuracy for reasons unrelated to data selection quality.

## Data and Splits

The scientist must use only the benchmark-provided versions of the eight datasets: 2dplanes, nomao, bbc-embedding, MiniBooNE, digits, election, electricity, and fried. The predefined train, validation, and test splits must remain fixed for each seed. No external labeled data, extra unlabeled data, alternate OpenML versions, or re-sampled test sets may be used.

## Ranking Inputs

The ranking method may use the training pool and validation set provided for that seed. It must not use test labels, test predictions, or aggregate test-set feedback to choose or tune the ranking. Test data is only for final evaluation of selected prefixes.

## Candidate Pool Size

The practical comparison must keep the benchmark pool sizes fixed: 50 training and 50 validation examples for standard datasets, 100 training and 100 validation examples for digits and bbc-embedding, and the corresponding fixed test sizes. The small-pool oracle comparison must keep 20 training examples, 100 validation examples, and 500 test examples. Increasing the candidate pool, validation pool, or test pool changes the problem.

## Random Seeds and Repeats

Use the benchmark seed schedule and report averages over the same 20 independent trials. Dropping hard seeds, adding extra seeds only for a submitted method, or selecting favorable runs is not allowed.

## Utility-Query and Retraining Budget

Non-oracle methods must respect the benchmark's model-retraining or subset-utility-query budget. Exact exhaustive dynamic programming is allowed only in the small-pool oracle experiment, where it is a reference point rather than a practical submitted method.

## Baseline Comparisons

Baseline results must be computed under the same splits, learner, preprocessing, and evaluation checkpoints as the submitted method. A comparison is invalid if the submitted method receives more data, more test feedback, or a different target learner than the baselines.

## Compliance Checklist

- [ ] Target learner is the benchmark Logistic Regression model.
- [ ] Only the eight benchmark datasets are used.
- [ ] Train, validation, and test splits match the benchmark seed files.
- [ ] Test labels and test feedback are not used to create or tune rankings.
- [ ] Candidate pool and validation sizes match the specified experiment.
- [ ] Results are averaged over the benchmark's 20 trials.
- [ ] Non-oracle utility-query and retraining budgets are not exceeded.
- [ ] Baselines and submitted method use the same preprocessing and evaluation checkpoints.
