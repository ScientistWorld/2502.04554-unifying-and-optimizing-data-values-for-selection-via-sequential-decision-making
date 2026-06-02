from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from data.tasks import load_task


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="digits", choices=["digits", "synthetic_planes"])
    parser.add_argument("--seed", type=int, default=10)
    parser.add_argument("--train-size", type=int, default=None)
    parser.add_argument("--output-dir", default="checkpoints/rankings")
    args = parser.parse_args()

    task = load_task(args.dataset, args.seed, train_size=args.train_size)
    rng = np.random.default_rng(args.seed)
    ranking = rng.permutation(len(task.x_train)).astype(int).tolist()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    payload = {
        "method": "random",
        "dataset": args.dataset,
        "seed": args.seed,
        "ranking": ranking,
        "train_size": len(task.x_train),
        "valid_size": len(task.x_valid),
        "test_size": len(task.x_test),
    }
    out = Path(args.output_dir) / f"random_{args.dataset}_seed{args.seed}.json"
    out.write_text(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()

