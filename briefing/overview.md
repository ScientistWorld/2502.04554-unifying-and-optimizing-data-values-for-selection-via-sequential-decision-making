# Overview

- **Paper ID:** 2502.04554
- **Title:** Unifying and Optimizing Data Values for Selection via Sequential-Decision-Making
- **Domain:** Data valuation / data selection / machine learning evaluation
- **TL;DR:** The paper reframes ranking-based data selection as a sequential optimization problem and proposes a practical utility surrogate for selecting small, high-value training subsets.

## Short Summary

The paper studies data valuation when the downstream use is selecting training examples under different subset budgets. It argues that a good ranking should perform well across the full selection curve, not just assign plausible standalone importance scores. The authors formalize this as a sequential decision problem whose cumulative reward is the sum of utilities over growing selected prefixes. They then connect existing game-theoretic data values to approximate dynamic programming and introduce a bipartite coverage surrogate to make the selection objective tractable at useful dataset sizes.

## Key Results

- Exact dynamic programming on small training sets exposes a noticeable gap between common data valuation rankings and the optimal sequential selection policy, especially at early budgets.
- Across eight OpenML-style datasets, the paper reports that the proposed practical selector improves mean test accuracy over Random, LOO, Influence, Data Shapley, Beta Shapley, Data Banzhaf, AME, DVRL, and Data-OOB in the main scaled experiment.
- Controlled curvature experiments support the claim that game-theoretic data values degrade as data points become more substitutable.
