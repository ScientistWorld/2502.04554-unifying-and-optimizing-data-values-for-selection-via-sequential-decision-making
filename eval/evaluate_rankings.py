from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

from data.metrics import selection_curve
from data.tasks import load_task


def summarize_curve(curve: list[float]) -> dict[str, float]:
    arr = np.array(curve, dtype=float)
    early_k = min(20, len(arr))
    return {
        "mean_accuracy": float(arr.mean()),
        "early20_accuracy": float(arr[:early_k].mean()),
        "final_accuracy": float(arr[-1]),
        "selection_budget": float(len(arr)),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rankings-dir", default="checkpoints/rankings")
    parser.add_argument("--scores", default="scoring/scores.json")
    parser.add_argument("--curves-dir", default="scoring/curves")
    parser.add_argument("--datasets", nargs="*", default=None)
    args = parser.parse_args()

    rankings_dir = Path(args.rankings_dir)
    curves_dir = Path(args.curves_dir)
    curves_dir.mkdir(parents=True, exist_ok=True)
    grouped: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)

    for path in sorted(rankings_dir.glob("*.json")):
        payload = json.loads(path.read_text())
        dataset = payload["dataset"]
        if args.datasets and dataset not in args.datasets:
            continue
        method = payload["method"]
        seed = int(payload["seed"])
        task = load_task(dataset, seed, train_size=int(payload["train_size"]))
        curve = selection_curve(task, [int(i) for i in payload["ranking"]], seed=seed)
        curve_payload = {"source": str(path), "curve": curve, "summary": summarize_curve(curve)}
        (curves_dir / f"{method}_{dataset}_seed{seed}.json").write_text(
            json.dumps(curve_payload, indent=2)
        )
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
