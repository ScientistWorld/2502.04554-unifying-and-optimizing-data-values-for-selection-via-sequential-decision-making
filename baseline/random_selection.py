"""Random baseline: a uniformly random order of the candidate pool."""
from __future__ import annotations

import argparse

import numpy as np

from data.instances import iter_instances, write_ranking


def rank_instance(instance: dict) -> list[int]:
    rng = np.random.default_rng(instance["seed"])
    return rng.permutation(len(instance["y_train"])).astype(int).tolist()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instances", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    for instance in iter_instances(args.instances):
        write_ranking(args.output_dir, instance["instance_id"], rank_instance(instance), method="random")


if __name__ == "__main__":
    main()
