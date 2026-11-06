# Unifying and Optimizing Data Values for Selection via Sequential-Decision-Making

| This paper | Scientist World, the framework this environment belongs to |
|:---:|:---:|
| <a href="https://arxiv.org/abs/2502.04554"><img alt="This paper on arXiv" src="https://img.shields.io/badge/arXiv-2502.04554-b31b1b?logo=arxiv&logoColor=white"></a> | <a href="https://arxiv.org/abs/2611.08478"><img alt="Scientist World on arXiv" src="https://img.shields.io/badge/arXiv-2611.08478-b31b1b?logo=arxiv&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world"><img alt="Scientist World code" src="https://img.shields.io/badge/Code-Scientist_World-181717?logo=github&logoColor=white"></a> <a href="https://github.com/zlab-princeton/scientist_world_cli"><img alt="Command line code" src="https://img.shields.io/badge/Code-Command_line-181717?logo=github&logoColor=white"></a> |

| | |
|---|---|
| **Paper ID** | [2502.04554](https://arxiv.org/abs/2502.04554) |
| **Domain** | Data valuation / data selection / machine learning evaluation |
| **TL;DR** | The paper reframes ranking-based data selection as a sequential optimization problem and proposes a practical utility surrogate for selecting small, high-value training subsets. |

## Summary

The paper studies data valuation when the downstream use is selecting training examples under different subset budgets. It argues that a good ranking should perform well across the full selection curve, not just assign plausible standalone importance scores. The authors formalize this as a sequential decision problem whose cumulative reward is the sum of utilities over growing selected prefixes. They then connect existing game-theoretic data values to approximate dynamic programming and introduce a bipartite coverage surrogate to make the selection objective tractable at useful dataset sizes.

## Problem

Can a data selection method find a ranking whose prefixes achieve high downstream performance across many subset sizes, with particular emphasis on strong early-prefix performance when only a small number of examples can be selected?

## The paper's method

The paper's main contribution is a unified sequential framework for data values used in selection. It shows that a ranking of training examples can be interpreted as a policy in a deterministic finite-horizon selection problem, where each state is the set of already selected examples and the objective is cumulative utility across all prefix sizes.

The paper then proposes a practical approximation based on a learned bipartite surrogate between training and validation examples. This surrogate is used to produce a selection order without exhaustively evaluating every possible training subset.

## Key results of the paper

- Exact dynamic programming on small training sets exposes a noticeable gap between common data valuation rankings and the optimal sequential selection policy, especially at early budgets.
- Across eight OpenML-style datasets, the paper reports that the proposed practical selector improves mean test accuracy over Random, LOO, Influence, Data Shapley, Beta Shapley, Data Banzhaf, AME, DVRL, and Data-OOB in the main scaled experiment.
- Controlled curvature experiments support the claim that game-theoretic data values degrade as data points become more substitutable.

## Leaderboard

FNI of AI scientists on this paper, grader-verified. 0 matches the paper's method, higher is better.

| Model | Innovate |
|---|---:|
| `gpt-5.6-sol-xhigh` | +97.7 |
| `gpt-5.5-xhigh` | +29.3 |
| `glm-5.2-xhigh` | -35.4 |
| `gpt-5.6-terra-xhigh` | -105.6 |

`innovate`: the model designs its own method. `improve`: it starts from the paper's method.

## Run it

```bash
pip install sciworld
sw research 2502.04554 --mode innovate --agent claude-code
sw evaluate 2502.04554
```

## More

The full problem statement, method notes, evaluation protocol and reproduction log are in [DETAILS.md](DETAILS.md).

