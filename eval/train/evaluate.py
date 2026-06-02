from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

from data.metrics import selection_curve
from data.tasks import load_task


TRAIN_SEEDS = tuple(range(1, 11))
SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def summarize_curve(curve: list[float]) -> dict[str, float]:
    arr = np.array(curve, dtype=float)
    early10_k = min(10, len(arr))
    early_k = min(20, len(arr))
    tail_start = min(early_k, len(arr) - 1)
    return {
        "mean_accuracy": float(arr.mean()),
        "early10_accuracy": float(arr[:early10_k].mean()),
        "early20_accuracy": float(arr[:early_k].mean()),
        "tail_accuracy": float(arr[tail_start:].mean()),
        "worst_prefix_accuracy": float(arr.min()),
        "max_accuracy_drop": float(max(0.0, -np.diff(arr).min())) if len(arr) > 1 else 0.0,
        "final_accuracy": float(arr[-1]),
        "selection_budget": float(len(arr)),
    }


def early_label_coverage(y_train: np.ndarray, ranking: list[int]) -> float:
    classes = set(int(cls) for cls in np.unique(y_train))
    if not classes:
        return 0.0
    early_k = min(20, len(ranking))
    prefix_classes = set(int(cls) for cls in y_train[np.array(ranking[:early_k], dtype=int)])
    return float(len(prefix_classes) / len(classes))


def safe_stem(value: str) -> str:
    return SAFE_NAME.sub("_", value).strip("_") or "unnamed"


def validate_ranking(ranking: list[int], train_size: int, source: Path) -> None:
    if len(ranking) != train_size:
        raise ValueError(f"{source} ranking has {len(ranking)} entries, expected {train_size}")
    if len(set(ranking)) != len(ranking):
        raise ValueError(f"{source} ranking contains duplicate indices")
    invalid = [idx for idx in ranking if idx < 0 or idx >= train_size]
    if invalid:
        raise ValueError(f"{source} ranking contains out-of-range indices: {invalid[:5]}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rankings-dir", default="checkpoints/rankings")
    parser.add_argument("--scores", default="scoring/scores_train.json")
    parser.add_argument("--curves-dir", default="scoring/curves_train")
    parser.add_argument("--datasets", nargs="*", default=None)
    parser.add_argument(
        "--seeds",
        nargs="*",
        type=int,
        default=list(TRAIN_SEEDS),
        help="Visible split seeds. Defaults to 1-10.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    rankings_dir = Path(args.rankings_dir)
    curves_dir = Path(args.curves_dir)
    curves_dir.mkdir(parents=True, exist_ok=True)
    seed_set = set(args.seeds)
    dataset_set = set(args.datasets) if args.datasets else None
    grouped: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)

    for path in sorted(rankings_dir.glob("*.json")):
        payload = json.loads(path.read_text())
        dataset = str(payload["dataset"])
        seed = int(payload["seed"])
        if dataset_set and dataset not in dataset_set:
            continue
        if seed not in seed_set:
            continue

        method = str(payload["method"])
        train_size = int(payload["train_size"])
        ranking = [int(i) for i in payload["ranking"]]
        validate_ranking(ranking, train_size, path)

        task = load_task(dataset, seed, train_size=train_size)
        curve = selection_curve(task, ranking, seed=seed)
        summary = summarize_curve(curve)
        summary["early_label_coverage"] = early_label_coverage(task.y_train, ranking)
        curve_payload = {
            "slice": "train",
            "source": str(path),
            "dataset": dataset,
            "method": method,
            "seed": seed,
            "curve": curve,
            "summary": summary,
        }
        curve_name = f"{safe_stem(method)}_{safe_stem(dataset)}_seed{seed}_train.json"
        (curves_dir / curve_name).write_text(json.dumps(curve_payload, indent=2))
        grouped[(dataset, method)].append(curve_payload["summary"])

    scores = {"experiments": {}}
    for (dataset, method), rows in sorted(grouped.items()):
        exp = f"{dataset}_selection"
        scores["experiments"].setdefault(exp, {"results": {}})
        metrics = {}
        for key in rows[0]:
            metrics[key] = float(np.mean([row[key] for row in rows]))
            if len(rows) > 1 and key == "mean_accuracy":
                metrics[f"{key}_std"] = float(np.std([row[key] for row in rows], ddof=0))
        scores["experiments"][exp]["results"][method] = metrics

    Path(args.scores).parent.mkdir(parents=True, exist_ok=True)
    Path(args.scores).write_text(json.dumps(scores, indent=2))


if __name__ == "__main__":
    main()
