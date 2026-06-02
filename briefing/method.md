# Paper's Method

## Key Contribution

The paper's main contribution is a unified sequential framework for data values used in selection. It shows that a ranking of training examples can be interpreted as a policy in a deterministic finite-horizon selection problem, where each state is the set of already selected examples and the objective is cumulative utility across all prefix sizes.

The paper then proposes a practical approximation based on a learned bipartite surrogate between training and validation examples. This surrogate is used to produce a selection order without exhaustively evaluating every possible training subset.

## Approach

The framework starts from the observation that ranking-based data values implicitly solve all prefix-budget selection problems at once. For a dataset `D` and utility function `U(S)`, the target objective is the average, equivalently the sum, of utilities over nested selected prefixes:

```text
maximize over permutations pi: sum_k U({pi(1), ..., pi(k)})
```

The exact formulation treats selected subsets as states, unselected training examples as actions, and subset utility as the reward signal. Backward dynamic programming computes the optimal value function and policy, then a forward pass converts the optimal trajectory into data values by assigning higher value to earlier selections. This exact solution is only feasible for small training pools because it requires utilities over exponentially many subsets.

The paper uses this formulation to reinterpret existing semi-value methods. Data Shapley, Beta Shapley, and Data Banzhaf can be viewed as approximate dynamic programming solutions that fit a linear utility surrogate and then act myopically by selecting the item with the largest fitted coefficient. This explains why these methods are optimal for linear utilities but can degrade when utility has high curvature and strong substitutability.

For the scalable method, the paper learns a bipartite graph between training examples and validation examples. Edges encode which validation examples a training example covers, using feature distance and matching labels with an adaptive threshold selected from sampled subset utilities. The resulting coverage utility is monotone submodular. The final selection is an iterative maximum-coverage process: repeatedly select the training example covering the most currently uncovered validation examples, remove the selected example and newly covered validation examples from consideration, and assign higher data values to earlier selected examples.

## Main Claims

- **Primary claim:** Optimizing data values for the sequential selection objective produces better selection curves than standard data valuation methods, especially for early prefixes.
- **Primary practical claim:** The bipartite surrogate closes much of the gap between tractable valuation methods and the optimal sequential policy while remaining computationally practical.
- **Secondary theoretical claim:** Existing semi-value methods are equivalent to myopic linear approximate dynamic programming policies for the sequential selection problem.
- **Secondary theoretical claim:** Under monotone submodular utility with curvature `c`, semi-value rankings have a `(1 - c)^2` approximation guarantee, explaining their degradation as substitutability increases.
