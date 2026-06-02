from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.metrics import fit_eval_logreg
from data.tasks import load_task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="digits", choices=["digits", "synthetic_planes"])
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--train-size", type=int, default=None)
    parser.add_argument("--output-dir", default="checkpoints/rankings")
    args = parser.parse_args()

    task = load_task(args.dataset, args.seed, train_size=args.train_size)
    full_acc = fit_eval_logreg(task.x_train, task.y_train, task.x_valid, task.y_valid, args.seed)
    values = []
    all_idx = np.arange(len(task.x_train))
    for i in range(len(task.x_train)):
        keep = all_idx[all_idx != i]
        without = fit_eval_logreg(
            task.x_train[keep], task.y_train[keep], task.x_valid, task.y_valid, args.seed + i + 1
        )
        values.append(full_acc - without)
    ranking = np.argsort(-np.array(values), kind="mergesort").astype(int).tolist()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "method": "loo",
        "dataset": args.dataset,
        "seed": args.seed,
        "ranking": ranking,
        "values": values,
        "train_size": len(task.x_train),
        "valid_size": len(task.x_valid),
        "test_size": len(task.x_test),
    }
    out = Path(args.output_dir) / f"loo_{args.dataset}_seed{args.seed}.json"
    out.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

