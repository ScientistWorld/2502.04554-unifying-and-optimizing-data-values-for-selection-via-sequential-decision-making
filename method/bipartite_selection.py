from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from sklearn.metrics import pairwise_distances

from data.instances import iter_instances, write_ranking
from data.metrics import fit_eval_logreg


def learn_bipartite_edges(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_valid: np.ndarray,
    y_valid: np.ndarray,
    seed: int,
    subset_samples: int,
    subset_size: int,
    n_thresholds: int,
) -> tuple[np.ndarray, dict]:
    """Algorithm 2: threshold feature/label edges by matching coverage to utility."""
    rng = np.random.default_rng(seed)
    distances = pairwise_distances(x_train, x_valid, metric="euclidean")
    label_match = y_train[:, None] == y_valid[None, :]
    lo, hi = float(distances.min()), float(distances.max())
    thresholds = np.linspace(lo, hi, n_thresholds)

    sampled_subsets = [
        rng.choice(len(x_train), size=min(subset_size, len(x_train)), replace=False)
        for _ in range(subset_samples)
    ]
    utilities = np.array(
        [
            fit_eval_logreg(x_train[idx], y_train[idx], x_valid, y_valid, seed + s)
            for s, idx in enumerate(sampled_subsets)
        ],
        dtype=float,
    )

    errors = []
    for tau in thresholds:
        edges = (distances <= tau) & label_match
        coverage = np.array(
            [np.any(edges[idx], axis=0).mean() for idx in sampled_subsets],
            dtype=float,
        )
        errors.append(float(np.mean(np.abs(coverage - utilities))))

    best_pos = int(np.argmin(errors))
    best_tau = float(thresholds[best_pos])
    best_edges = (distances <= best_tau) & label_match
    return best_edges, {
        "threshold": best_tau,
        "threshold_errors": errors,
        "subset_samples": subset_samples,
        "subset_size": subset_size,
        "n_thresholds": n_thresholds,
        "mean_validation_utility": float(utilities.mean()),
    }


def greedy_maximum_coverage(edges: np.ndarray) -> tuple[list[int], list[int]]:
    """Rank training points by iterative maximum uncovered validation coverage."""
    n_train = edges.shape[0]
    uncovered = np.ones(edges.shape[1], dtype=bool)
    remaining = set(range(n_train))
    ranking: list[int] = []
    gains: list[int] = []
    while remaining:
        best = max(
            remaining,
            key=lambda i: (int(np.sum(edges[i] & uncovered)), -i),
        )
        gain = int(np.sum(edges[best] & uncovered))
        ranking.append(best)
        gains.append(gain)
        uncovered &= ~edges[best]
        remaining.remove(best)
    return ranking, gains


def rank_instance(
    instance: dict,
    subset_samples: int = 80,
    subset_size: int | None = None,
    n_thresholds: int = 25,
) -> tuple[list[int], dict]:
    """Learn the bipartite surrogate for one instance and rank its pool."""
    n_train = len(instance["y_train"])
    subset_size = subset_size or max(2, min(n_train // 5, 20))
    edges, graph_info = learn_bipartite_edges(
        instance["x_train"],
        instance["y_train"],
        instance["x_valid"],
        instance["y_valid"],
        seed=instance["seed"],
        subset_samples=subset_samples,
        subset_size=subset_size,
        n_thresholds=n_thresholds,
    )
    ranking, gains = greedy_maximum_coverage(edges)
    return ranking, {"coverage_gains": gains, "graph": graph_info}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Bipartite-surrogate sequential selection ranker (see data/instances.py)."
    )
    parser.add_argument("--instances", required=True, help="directory of instance .npz files")
    parser.add_argument("--output-dir", required=True, help="where <instance_id>.json rankings go")
    parser.add_argument("--subset-samples", type=int, default=80)
    parser.add_argument("--subset-size", type=int, default=None)
    parser.add_argument("--thresholds", type=int, default=25)
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    for instance in iter_instances(args.instances):
        ranking, info = rank_instance(
            instance,
            subset_samples=args.subset_samples,
            subset_size=args.subset_size,
            n_thresholds=args.thresholds,
        )
        write_ranking(output_dir, instance["instance_id"], ranking, method="bipartite", **info)


if __name__ == "__main__":
    main()
