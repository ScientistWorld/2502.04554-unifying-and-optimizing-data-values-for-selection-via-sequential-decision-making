from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.metrics import fit_eval_logreg
from data.tasks import load_task


def permutation_shapley_values(
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_valid: np.ndarray,
    y_valid: np.ndarray,
    seed: int,
    permutations: int,
) -> list[float]:
    """Monte Carlo Data Shapley via random-permutation marginal utilities."""
    rng = np.random.default_rng(seed)
    n_train = len(x_train)
    values = np.zeros(n_train, dtype=float)
    for p in range(permutations):
        order = rng.permutation(n_train)
        previous_utility = 0.0
        prefix: list[int] = []
        for step, idx in enumerate(order):
            prefix.append(int(idx))
            current_utility = fit_eval_logreg(
                x_train[np.array(prefix, dtype=int)],
                y_train[np.array(prefix, dtype=int)],
                x_valid,
                y_valid,
                seed + p * n_train + step,
            )
            values[idx] += current_utility - previous_utility
            previous_utility = current_utility
    values /= max(1, permutations)
    return values.tolist()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="digits", choices=["digits", "synthetic_planes"])
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--train-size", type=int, default=None)
    parser.add_argument("--permutations", type=int, default=8)
    parser.add_argument("--output-dir", default="checkpoints/rankings")
    args = parser.parse_args()

    task = load_task(args.dataset, args.seed, train_size=args.train_size)
    values = permutation_shapley_values(
        task.x_train,
        task.y_train,
        task.x_valid,
        task.y_valid,
        seed=args.seed,
        permutations=args.permutations,
    )
    ranking = np.argsort(-np.array(values), kind="mergesort").astype(int).tolist()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "method": "datashap",
        "dataset": args.dataset,
        "seed": args.seed,
        "ranking": ranking,
        "values": values,
        "permutations": args.permutations,
        "train_size": len(task.x_train),
        "valid_size": len(task.x_valid),
        "test_size": len(task.x_test),
    }
    out = Path(args.output_dir) / f"datashap_{args.dataset}_seed{args.seed}.json"
    out.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
