# Research Direction

## Research Problem

This benchmark is about ranking training examples for data selection. The central question is whether a method can produce a single ordering whose prefixes perform well across multiple selection budgets for a fixed downstream learner.

## Core Contribution Scope

A scientist should work on methods that improve data valuation or data ranking for prefix-based selection. The contribution should change how the ordering is produced, how validation utility is modeled, how dependencies between examples are captured, or how selection quality across budgets is optimized.

## Approach Scope

In-scope work includes new valuation functions, utility surrogates, subset-ranking objectives, sequential selection policies, diversity-aware selection rules, or improved ways to estimate utility from the allowed training and validation data. The method may be deterministic or learned, exact or approximate, as long as it outputs an ordered list of the fixed candidate training pool and respects the evaluation constraints.

## Out of Bounds

- Changing the task from ordered data selection to model architecture search, hyperparameter optimization, or data augmentation.
- Improving scores by replacing the fixed downstream learner with a stronger model.
- Using external data or test-set feedback to construct the ranking.
- Reporting only a single best-budget subset when the benchmark requires a complete ranking and prefix curve.
- Exhaustively searching all possible rankings for the scaled benchmark.
