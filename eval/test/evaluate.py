from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

from data.metrics import selection_curve
from data.tasks import load_task


TEST_SEEDS = tuple(range(11, 21))
SAFE_NAME = re.compile(r"[^A-Za-z0-9_.-]+")


def summarize_curve(curve: list[float]) -> dict[str, float]:
    arr = np.array(curve, dtype=float)
    early_k = min(20, len(arr))
    return {
        "mean_accuracy": float(arr.mean()),
        "early20_accuracy": float(arr[:early_k].mean()),
        "final_accuracy": float(arr[-1]),
        "selection_budget": float(len(arr)),
    }


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


def methods_from_train_scores(
    train_scores_path: Path,
    dataset_set: set[str] | None,
) -> dict[str, set[str]]:
    if not train_scores_path.exists():
        return {}

    train_scores = json.loads(train_scores_path.read_text())
    wanted: dict[str, set[str]] = {}
    for exp_name, exp_payload in train_scores.get("experiments", {}).items():
        suffix = "_selection"
        if not exp_name.endswith(suffix):
            continue
        dataset = exp_name[: -len(suffix)]
        if dataset_set and dataset not in dataset_set:
            continue
        methods = set(exp_payload.get("results", {}).keys())
        if methods:
            wanted[dataset] = methods
    return wanted


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rankings-dir", default="checkpoints/rankings")
    parser.add_argument("--scores", default="scoring/scores_test.json")
    parser.add_argument("--curves-dir", default="scoring/curves_test")
    parser.add_argument("--datasets", nargs="*", default=None)
    parser.add_argument("--train-scores", default="scoring/scores_train.json")
    parser.add_argument(
        "--seeds",
        nargs="*",
        type=int,
        default=list(TEST_SEEDS),
        help="Held-out split seeds. Defaults to 11-20.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    rankings_dir = Path(args.rankings_dir)
    curves_dir = Path(args.curves_dir)
    curves_dir.mkdir(parents=True, exist_ok=True)
    seed_set = set(args.seeds)
    dataset_set = set(args.datasets) if args.datasets else None
    expected_methods = methods_from_train_scores(Path(args.train_scores), dataset_set)
    grouped: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)

    for path in sorted(rankings_dir.glob("*.json")):
        payload = json.loads(path.read_text())
        dataset = str(payload["dataset"])
        method = str(payload["method"])
        seed = int(payload["seed"])
        if dataset_set and dataset not in dataset_set:
            continue
        if seed not in seed_set:
            continue
        if expected_methods and method not in expected_methods.get(dataset, set()):
            continue

        train_size = int(payload["train_size"])
        ranking = [int(i) for i in payload["ranking"]]
        validate_ranking(ranking, train_size, path)

        task = load_task(dataset, seed, train_size=train_size)
        curve = selection_curve(task, ranking, seed=seed)
        curve_payload = {
            "slice": "test",
            "source": str(path),
            "dataset": dataset,
            "method": method,
            "seed": seed,
            "curve": curve,
            "summary": summarize_curve(curve),
        }
        curve_name = f"{safe_stem(method)}_{safe_stem(dataset)}_seed{seed}_test.json"
        (curves_dir / curve_name).write_text(json.dumps(curve_payload, indent=2))
        grouped[(dataset, method)].append(curve_payload["summary"])

    if expected_methods:
        missing = []
        for dataset, methods in sorted(expected_methods.items()):
            for method in sorted(methods):
                if (dataset, method) not in grouped:
                    missing.append(f"{dataset}:{method}")
        if missing:
            raise ValueError(
                "held-out test rankings are missing for methods scored on train: "
                + ", ".join(missing)
            )

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
