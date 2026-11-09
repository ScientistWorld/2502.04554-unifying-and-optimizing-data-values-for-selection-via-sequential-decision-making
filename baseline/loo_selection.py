"""Leave-one-out baseline: rank points by U(D) - U(D minus i) on validation."""
from __future__ import annotations

import argparse

import numpy as np

from data.instances import iter_instances, write_ranking
from data.metrics import fit_eval_logreg


def loo_values(instance: dict) -> list[float]:
    x_train, y_train = instance["x_train"], instance["y_train"]
    x_valid, y_valid = instance["x_valid"], instance["y_valid"]
    seed = instance["seed"]
    full_acc = fit_eval_logreg(x_train, y_train, x_valid, y_valid, seed)
    all_idx = np.arange(len(x_train))
    values = []
    for i in range(len(x_train)):
        keep = all_idx[all_idx != i]
        without = fit_eval_logreg(x_train[keep], y_train[keep], x_valid, y_valid, seed + i + 1)
        values.append(full_acc - without)
    return values


def rank_instance(instance: dict) -> tuple[list[int], list[float]]:
    values = loo_values(instance)
    ranking = np.argsort(-np.array(values), kind="mergesort").astype(int).tolist()
    return ranking, values


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    for instance in iter_instances(args.instances):
        ranking, values = rank_instance(instance)
        write_ranking(args.output_dir, instance["instance_id"], ranking, method="loo", values=values)


if __name__ == "__main__":
    main()
