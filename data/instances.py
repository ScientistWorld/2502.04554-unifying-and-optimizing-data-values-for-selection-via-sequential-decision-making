"""Instance files and the ranker interface shared by every selection method.

An *instance* is what a selection method is allowed to see for one split:
the candidate training pool and the validation set (features and labels),
plus an integer ``seed`` the method may use for its own randomness. Test data
is never part of an instance.

Instance file: ``<instances_dir>/<instance_id>.npz`` with arrays
``x_train`` (n, d) float, ``y_train`` (n,) int, ``x_valid`` (m, d) float,
``y_valid`` (m,) int, and scalars ``dataset`` (str), ``instance_id`` (str),
``seed`` (int).

Ranker contract: a ranker is an executable shell script in ``scripts/rankers/``
called as ``bash scripts/rankers/<name>.sh INSTANCES_DIR OUTPUT_DIR``. For every
instance file it must write ``OUTPUT_DIR/<instance_id>.json`` containing
``{"ranking": [...]}`` -- a permutation of ``0..n-1`` (JSON integers) giving the
order in which the candidate training points are selected. Any other fields
are ignored by the evaluators. The file stem is the method name.

``python -m data.instances OUT_DIR [--datasets ...] [--seeds ...]`` writes the
visible development instances.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterator

import numpy as np

from data.tasks import DATASETS, SelectionTask, load_task


DEFAULT_VISIBLE_SEEDS = tuple(range(1, 21))


def instance_id(dataset: str, seed: int) -> str:
    return f"{dataset}_v{seed:03d}"


def write_instance(directory: Path, task: SelectionTask, inst_id: str, seed: int) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{inst_id}.npz"
    np.savez(
        path,
        x_train=np.asarray(task.x_train, dtype=np.float64),
        y_train=np.asarray(task.y_train, dtype=np.int64),
        x_valid=np.asarray(task.x_valid, dtype=np.float64),
        y_valid=np.asarray(task.y_valid, dtype=np.int64),
        dataset=np.array(task.name),
        instance_id=np.array(inst_id),
        seed=np.array(int(seed), dtype=np.int64),
    )
    return path


def read_instance(path: Path) -> dict:
    with np.load(path, allow_pickle=False) as data:
        return {
            "x_train": data["x_train"],
            "y_train": data["y_train"].astype(int),
            "x_valid": data["x_valid"],
            "y_valid": data["y_valid"].astype(int),
            "dataset": str(data["dataset"]),
            "instance_id": str(data["instance_id"]),
            "seed": int(data["seed"]),
        }


def iter_instances(directory: Path | str) -> Iterator[dict]:
    paths = sorted(Path(directory).glob("*.npz"))
    if not paths:
        raise FileNotFoundError(f"no instance files (*.npz) found in {directory}")
    for path in paths:
        yield read_instance(path)


def write_ranking(output_dir: Path | str, inst_id: str, ranking, **extra) -> Path:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = {"ranking": [int(i) for i in ranking], **extra}
    path = output_dir / f"{inst_id}.json"
    path.write_text(json.dumps(payload))
    return path


def write_visible_instances(
    directory: Path | str,
    datasets=DATASETS,
    seeds=DEFAULT_VISIBLE_SEEDS,
) -> list[Path]:
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for stale in directory.glob("*.npz"):
        stale.unlink()
    paths = []
    for dataset in datasets:
        for seed in seeds:
            task = load_task(dataset, int(seed))
            paths.append(write_instance(directory, task, instance_id(dataset, int(seed)), int(seed)))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("output_dir")
    parser.add_argument("--datasets", nargs="*", default=list(DATASETS))
    parser.add_argument("--seeds", nargs="*", type=int, default=list(DEFAULT_VISIBLE_SEEDS))
    args = parser.parse_args()
    paths = write_visible_instances(args.output_dir, args.datasets, args.seeds)
    print(f"wrote {len(paths)} instance files to {args.output_dir}")


if __name__ == "__main__":
    main()
