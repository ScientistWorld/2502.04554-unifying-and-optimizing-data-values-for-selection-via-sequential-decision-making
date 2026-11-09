"""Visible (train-slice) evaluation of every registered ranker.

For each visible instance (``data.tasks.load_task(dataset, seed)`` for the
visible seeds) this writes the instance inputs, runs every ranker found in
``scripts/rankers/*.sh`` through the ranker contract in ``data/instances.py``,
validates each returned ranking, retrains the fixed target learner on every
prefix of the ranking, and scores the test-accuracy selection curve.

Only rankings are read from rankers; every score is recomputed here.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

from data.instances import DEFAULT_VISIBLE_SEEDS, instance_id, method_seed, write_instance
from data.metrics import selection_curve
from data.tasks import DATASETS, load_task


ROOT = Path(__file__).resolve().parents[2]
SCORED_METRICS = (
    "mean_accuracy",
    "early10_accuracy",
    "early20_accuracy",
    "tail_accuracy",
    "max_accuracy_drop",
)


def summarize_curve(curve: list[float]) -> dict[str, float]:
    arr = np.array(curve, dtype=float)
    diffs = np.diff(arr)
    return {
        "mean_accuracy": float(arr.mean()),
        "early10_accuracy": float(arr[:10].mean()),
        "early20_accuracy": float(arr[:20].mean()),
        "tail_accuracy": float(arr[20:].mean()),
        "max_accuracy_drop": float(max(0.0, float(-diffs.min()))) if len(diffs) else 0.0,
    }


def aggregate(rows: list[dict], curves: list[list[float]]) -> dict[str, float]:
    out = {key: float(np.mean([row[key] for row in rows])) for key in SCORED_METRICS}
    # Pooled spread of accuracy over all prefixes and instances (the paper's +/-).
    out["curve_accuracy_std"] = float(np.std(np.concatenate([np.asarray(c) for c in curves])))
    return out


def validate_ranking(raw, n_train: int, where: str) -> list[int]:
    if not isinstance(raw, list):
        raise ValueError(f"{where}: 'ranking' must be a JSON list")
    if len(raw) != n_train:
        raise ValueError(f"{where}: ranking has {len(raw)} entries, the pool has {n_train}")
    for value in raw:
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{where}: ranking entries must be JSON integers, got {value!r}")
    if sorted(raw) != list(range(n_train)):
        raise ValueError(f"{where}: ranking is not a permutation of 0..{n_train - 1}")
    return list(raw)


def discover_rankers(rankers_dir: Path, only: list[str] | None) -> dict[str, Path]:
    found = {p.stem: p for p in sorted(rankers_dir.glob("*.sh"))}
    if only:
        missing = sorted(set(only) - set(found))
        if missing:
            raise SystemExit(f"requested rankers not found in {rankers_dir}: {missing}")
        found = {name: found[name] for name in only}
    if not found:
        raise SystemExit(f"no rankers (*.sh) found in {rankers_dir}")
    return found


def run_ranker(name: str, script: Path, instances_dir: Path, out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)
    print(f"[train] running ranker {name}", flush=True)
    proc = subprocess.run(
        ["bash", str(script.resolve()), str(instances_dir.resolve()), str(out_dir.resolve())],
        cwd=ROOT,
    )
    if proc.returncode != 0:
        raise SystemExit(f"ranker {name} exited with status {proc.returncode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--rankers-dir", default="scripts/rankers")
    parser.add_argument("--rankers", nargs="*", default=None, help="subset of ranker names")
    parser.add_argument("--scores", default="scoring/scores_train.json")
    parser.add_argument("--curves-dir", default="scoring/curves_train")
    parser.add_argument("--instances-dir", default="checkpoints/instances/train")
    parser.add_argument("--rankings-dir", default="checkpoints/rankings/train")
    parser.add_argument("--datasets", nargs="*", default=list(DATASETS))
    parser.add_argument("--seeds", nargs="*", type=int, default=list(DEFAULT_VISIBLE_SEEDS))
    parser.add_argument(
        "--skip-run",
        action="store_true",
        help="score rankings already present in --rankings-dir instead of rerunning rankers",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rankers = discover_rankers(Path(args.rankers_dir), args.rankers)
    instances_dir = Path(args.instances_dir)
    rankings_dir = Path(args.rankings_dir)
    curves_dir = Path(args.curves_dir)

    tasks = {}
    for dataset in args.datasets:
        for seed in args.seeds:
            tasks[instance_id(dataset, seed)] = (dataset, seed, load_task(dataset, seed))

    if not args.skip_run:
        if instances_dir.exists():
            shutil.rmtree(instances_dir)
        instances_dir.mkdir(parents=True)
        for inst_id, (dataset, seed, task) in tasks.items():
            write_instance(instances_dir, task, inst_id, method_seed(seed))
        for name, script in rankers.items():
            run_ranker(name, script, instances_dir, rankings_dir / name)

    curves_dir.mkdir(parents=True, exist_ok=True)
    for stale in curves_dir.glob("*.json"):
        stale.unlink()

    scores: dict = {"experiments": {}}
    for name in rankers:
        per_dataset_rows: dict[str, list[dict]] = defaultdict(list)
        per_dataset_curves: dict[str, list[list[float]]] = defaultdict(list)
        records = []
        for inst_id, (dataset, seed, task) in tasks.items():
            path = rankings_dir / name / f"{inst_id}.json"
            if not path.is_file():
                raise SystemExit(f"ranker {name} wrote no ranking for instance {inst_id}")
            payload = json.loads(path.read_text())
            if not isinstance(payload, dict):
                raise SystemExit(f"{path}: output must be a JSON object")
            ranking = validate_ranking(payload.get("ranking"), len(task.y_train), str(path))
            curve = selection_curve(task, ranking, seed=seed)
            summary = summarize_curve(curve)
            per_dataset_rows[dataset].append(summary)
            per_dataset_curves[dataset].append(curve)
            records.append({"instance_id": inst_id, "dataset": dataset, "summary": summary, "curve": curve})
        for dataset, rows in per_dataset_rows.items():
            exp = scores["experiments"].setdefault(f"{dataset}_selection", {"results": {}})
            exp["results"][name] = aggregate(rows, per_dataset_curves[dataset])
        (curves_dir / f"{name}.json").write_text(json.dumps({"slice": "train", "method": name, "instances": records}))

    Path(args.scores).parent.mkdir(parents=True, exist_ok=True)
    Path(args.scores).write_text(json.dumps(scores, indent=2, sort_keys=True))
    print(f"[train] wrote {args.scores}", file=sys.stderr)


if __name__ == "__main__":
    main()
