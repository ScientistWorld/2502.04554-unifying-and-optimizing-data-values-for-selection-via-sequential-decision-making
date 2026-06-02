from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from sklearn.metrics import pairwise_distances

from data.metrics import fit_eval_logreg
from data.tasks import load_task


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


def run(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    task = load_task(args.dataset, args.seed, train_size=args.train_size)
    subset_size = args.subset_size or max(2, min(len(task.x_train) // 5, 20))
    edges, graph_info = learn_bipartite_edges(
        task.x_train,
        task.y_train,
        task.x_valid,
        task.y_valid,
        seed=args.seed,
        subset_samples=args.subset_samples,
        subset_size=subset_size,
        n_thresholds=args.thresholds,
    )
    ranking, gains = greedy_maximum_coverage(edges)
    payload = {
        "method": "bipartite",
        "dataset": args.dataset,
        "seed": args.seed,
        "ranking": ranking,
        "coverage_gains": gains,
        "graph": graph_info,
        "train_size": len(task.x_train),
        "valid_size": len(task.x_valid),
        "test_size": len(task.x_test),
    }
    (output_dir / f"bipartite_{args.dataset}_seed{args.seed}.json").write_text(
        json.dumps(payload, indent=2)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="digits", choices=["digits", "synthetic_planes"])
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--train-size", type=int, default=None)
    parser.add_argument("--subset-samples", type=int, default=80)
    parser.add_argument("--subset-size", type=int, default=None)
    parser.add_argument("--thresholds", type=int, default=25)
    parser.add_argument("--output-dir", default="checkpoints/rankings")
    run(parser.parse_args())


if __name__ == "__main__":
    main()

