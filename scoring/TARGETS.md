# Evaluation Targets

The benchmark evaluates ordered data selection. A submitted method receives the same candidate training pool, validation set, downstream learner, and evaluation splits as the reproduction, then outputs a single ranking of training examples.

The experiment headings below match the current `scoring/reference.json` experiment keys. Each experiment includes both benefit metrics and constraint metrics so future improvements cannot come only from using a larger selection budget or unstable runs.

## Primary: digits_selection

Tests sequential data selection on the handwritten-digits benchmark under the paper's practical evaluation protocol.

- **Benefit metrics:** mean_accuracy, early10_accuracy, early20_accuracy, tail_accuracy, worst_prefix_accuracy, final_accuracy, and early_label_balance (higher is better)
- **Constraint metrics:** mean_accuracy_std, max_accuracy_drop, and selection_budget (lower is better)
- **How to run evaluation:** Rank the fixed digits training pool for each seed, retrain the fixed target learner on selected prefixes, evaluate on the fixed test split, and aggregate over the benchmark trials.

## Primary: synthetic_planes_selection

Tests sequential data selection on a structured tabular multiclass benchmark analogous to the paper's smaller structured-data settings.

- **Benefit metrics:** mean_accuracy, early10_accuracy, early20_accuracy, tail_accuracy, worst_prefix_accuracy, final_accuracy, and early_label_balance (higher is better)
- **Constraint metrics:** mean_accuracy_std, max_accuracy_drop, and selection_budget (lower is better)
- **How to run evaluation:** Rank the fixed synthetic-planes training pool for each seed, retrain the fixed target learner on selected prefixes, evaluate on the fixed test split, and aggregate over the benchmark trials.
