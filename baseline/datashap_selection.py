"""Monte Carlo Data Shapley baseline (random-permutation marginal utilities)."""
from __future__ import annotations

import argparse

import numpy as np

from data.instances import iter_instances, write_ranking
from data.metrics import fit_eval_logreg


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


def rank_instance(instance: dict, permutations: int = 8) -> tuple[list[int], list[float]]:
    values = permutation_shapley_values(
        instance["x_train"],
        instance["y_train"],
        instance["x_valid"],
        instance["y_valid"],
        seed=instance["seed"],
        permutations=permutations,
    )
    ranking = np.argsort(-np.array(values), kind="mergesort").astype(int).tolist()
    return ranking, values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--permutations", type=int, default=8)
    args = parser.parse_args()
    for instance in iter_instances(args.instances):
        ranking, values = rank_instance(instance, args.permutations)
        write_ranking(
            args.output_dir,
            instance["instance_id"],
            ranking,
            method="datashap",
            values=values,
            permutations=args.permutations,
        )


if __name__ == "__main__":
    main()
