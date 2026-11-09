# Experiment Overview

The section headings match the experiment keys in `scoring/reference.json`. Each experiment is scored on 100 held-out instances (random splits) that methods have not seen; the visible slice uses seeds 1-20 of the same generators.

## digits_selection

Establishes whether a selection method finds orderings of a multiclass image-style candidate pool whose prefixes train a good classifier at every budget, and especially at very small budgets where only a handful of the 10 classes' examples can be chosen. Ten classes and a 100-point pool make early choices consequential: a poor early ordering leaves classes unseen or poorly represented for many steps. The tail metric checks that early-budget gains are not paid for at larger budgets, and the step-drop metric checks that the curve does not regress as data is added.

## fried_selection

Establishes the same question on a smooth, low-noise binary tabular problem with five informative and five irrelevant features and a 50-point pool. Here class coverage is easy, so differences come from choosing examples that pin down the decision boundary early and from avoiding harmful additions later. It checks that an improvement is not specific to multiclass coverage effects.
