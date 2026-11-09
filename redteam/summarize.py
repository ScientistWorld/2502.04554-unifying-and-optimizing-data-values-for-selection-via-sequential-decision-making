"""Reporting only: these coefficients are never used to construct methods."""
from __future__ import annotations

import json
import math
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "redteam"


def metrics(path):
    raw = json.loads(path.read_text())
    return {exp: content["results"]["bipartite"]
            for exp, content in raw["experiments"].items()}


def main():
    reference = json.loads((ROOT / "scoring/reference.json").read_text())["experiments"]
    records, values = {}, {}
    for path in sorted(AUDIT.glob("*/run_record.json")):
        name = path.parent.name
        records[name] = json.loads(path.read_text())
        score_path = path.parent / "scores_test.json"
        if records[name].get("test_exit_code") == 0 and score_path.exists():
            values[name] = metrics(score_path)
    base = values["reference_seed0"]
    scales = {}
    for exp, definition in reference.items():
        scales[exp] = {}
        for key, spec in definition["metrics"].items():
            if abs(spec["coefficient"]) == 0:
                continue
            numbers = [row[exp][key] for row in values.values()]
            spread = statistics.pstdev(numbers)
            scales[exp][key] = spread if spread > 1e-15 else None
    ranks, contributions = {}, {}
    for name, row in values.items():
        components = {}
        for exp, definition in reference.items():
            for key, spec in definition["metrics"].items():
                coefficient = abs(spec["coefficient"])
                if coefficient == 0:
                    continue
                scale = scales[exp][key]
                delta = row[exp][key] - base[exp][key]
                if not spec["higher_is_better"]:
                    delta *= -1
                components[f"{exp}/{key}"] = (
                    definition["weight"] * coefficient * delta / scale if scale else 0.0)
        ranks[name] = sum(components.values())
        contributions[name] = components
    reference_names = ["reference_seed0", "reference_seed1", "reference_seed2"]
    seed_spread = {}
    for exp in base:
        means = [values[name][exp]["mean_accuracy"] for name in reference_names]
        seed_spread[exp] = {
            "mean_accuracies": means, "min": min(means), "max": max(means),
            "range": max(means) - min(means), "population_std": statistics.pstdev(means),
        }
    seed_ranks = [ranks[name] for name in reference_names]
    summary = {
        "normalization": "population standard deviation over listed accepted audit attempts; future production population unknown",
        "cohort": list(values), "scales": scales, "scores": ranks,
        "raw_metrics": values, "weighted_metric_contributions": contributions,
        "reference_seed_spread": seed_spread,
        "reference_rank_spread": {"scores": seed_ranks, "range": max(seed_ranks)-min(seed_ranks)},
        "rejected": {name: r for name, r in records.items() if r.get("test_exit_code") != 0},
        "all_evaluators_unchanged": all(r.get("evaluator_unchanged") for r in records.values()),
    }
    (AUDIT / "summary.json").write_text(json.dumps(summary, indent=2))
    lines = ["| Attempt | digits mean | synthetic mean | Audit normalized gain | Test |",
             "|---|---:|---:|---:|---|"]
    for name in records:
        if name in values:
            row = values[name]
            lines.append(f"| {name} | {row['digits_selection']['mean_accuracy']:.6f} | "
                         f"{row['synthetic_planes_selection']['mean_accuracy']:.6f} | {ranks[name]:+.6f} | accepted |")
        else:
            lines.append(f"| {name} | — | — | — | rejected |")
    (AUDIT / "results.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines), flush=True)
    print(json.dumps({"seed_spread": seed_spread, "rank_spread": summary["reference_rank_spread"]}), flush=True)


if __name__ == "__main__":
    main()
