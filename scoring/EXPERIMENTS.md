# Experiment Overview

The section headings here match the current experiment keys in `scoring/reference.json`. These descriptions explain the scientific purpose of each benchmark measurement without requiring or revealing any particular selection algorithm.

## digits_selection

Tests whether a data selection method can produce a ranking that performs well on an image-style multiclass classification task with a larger candidate pool. This experiment emphasizes the low-budget and full-curve behavior of the ranking, while also tracking variability and selected-budget size so gains are not credited solely for unstable or larger-budget behavior.

## synthetic_planes_selection

Tests whether a data selection method can produce a ranking that performs well on a structured tabular binary-classification task. This experiment provides a smaller practical setting for comparing full-curve accuracy, early-prefix quality, run-to-run stability, and selected-budget size under the same fixed learner and split protocol.
