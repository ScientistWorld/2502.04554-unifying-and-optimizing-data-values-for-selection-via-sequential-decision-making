"""Summarize the hardening checks: composite gains, paired noise, failures.

Composite gain of attempt a over the reference r (the rule the gym's rank uses):
    sum_exp weight_exp * sum_metric |coef| * dir * (v_a - v_r) / sigma_exp,metric
with dir = +1 if higher_is_better else -1 and sigma the population std of the
aggregate metric across the scored attempts listed here. Since every aggregate
is a mean over held-out instances, the same expression evaluated per instance
gives a paired per-instance gain whose mean equals the composite; its standard
error is the paired noise of the test.

Writes redteam/hardening/summary.json and summary.md. Per-instance curves are
read from tmp/hardening/ and never copied into the repository.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "redteam" / "hardening"
TMP = ROOT / "tmp" / "hardening"


def load(path: Path):
    return json.loads(path.read_text()) if path.exists() else None


def mean(xs):
    return sum(xs) / len(xs)


def pstd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


def sstd(xs):
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def main() -> None:
    ref = load(ROOT / "scoring" / "reference.json")["experiments"]
    scored = {
        exp: {m: d for m, d in spec["metrics"].items() if abs(d["coefficient"]) > 0}
        for exp, spec in ref.items()
    }
    weights = {exp: spec["weight"] for exp, spec in ref.items()}

    attempts: dict[str, dict] = {}       # name -> {exp: {metric: value}}
    per_instance: dict[str, dict] = {}   # name -> {exp: {instance_id: summary}}
    records = {}
    for folder in sorted(p for p in OUT.iterdir() if p.is_dir()):
        record = load(folder / "record.json")
        if record is None:
            continue
        records[folder.name] = record
        scores = load(folder / "scores_test.json")
        if scores is None:
            continue
        for exp, payload in scores["experiments"].items():
            for method, metrics in payload["results"].items():
                key = method if folder.name == "cohort" else f"{folder.name}:{method}"
                attempts.setdefault(key, {})[exp] = metrics
                curves = load(TMP / folder.name / "curves_test" / f"{method}.json")
                if curves:
                    for row in curves["instances"]:
                        if f"{row['dataset']}_selection" == exp:
                            per_instance.setdefault(key, {}).setdefault(exp, {})[row["instance_id"]] = row["summary"]

    reference_name = "bipartite"
    if reference_name not in attempts:
        raise SystemExit("cohort results for the reference are missing")
    # Duplicated reference runs inside shortcut checks are identity checks, not attempts.
    cohort_names = [a for a in attempts if not a.endswith(":bipartite")]

    sigma = {
        exp: {m: pstd([attempts[a][exp][m] for a in cohort_names]) for m in scored[exp]}
        for exp in scored
    }

    def direction(exp, metric):
        return 1.0 if ref[exp]["metrics"][metric]["higher_is_better"] else -1.0

    def contribution(exp, values, base):
        total = 0.0
        for metric, spec in scored[exp].items():
            if sigma[exp][metric] > 0:
                total += abs(spec["coefficient"]) * direction(exp, metric) * (values[metric] - base[metric]) / sigma[exp][metric]
        return total

    summary = {"normalization": "population std of each aggregate metric over the scored attempts below",
               "attempts": cohort_names, "sigma": sigma, "results": {}}
    for name in attempts:
        entry = {"metrics": attempts[name], "composite_gain": 0.0, "per_experiment": {}}
        se_sq = 0.0
        for exp in scored:
            gain = contribution(exp, attempts[name][exp], attempts[reference_name][exp])
            entry["per_experiment"][exp] = {"gain": gain}
            entry["composite_gain"] += weights[exp] * gain
            inst_a = per_instance.get(name, {}).get(exp)
            inst_r = per_instance.get(reference_name, {}).get(exp)
            if inst_a and inst_r and set(inst_a) == set(inst_r) and name != reference_name:
                ids = sorted(inst_a)
                diffs = [contribution(exp, inst_a[i], inst_r[i]) for i in ids]
                sd = sstd(diffs)
                se = sd / math.sqrt(len(ids))
                se_sq += (weights[exp] * se) ** 2
                acc = [inst_a[i]["mean_accuracy"] - inst_r[i]["mean_accuracy"] for i in ids]
                acc_se = sstd(acc) / math.sqrt(len(ids))
                entry["per_experiment"][exp].update({
                    "n_instances": len(ids),
                    "paired_gain_se": se,
                    "mean_accuracy_diff": mean(acc),
                    "mean_accuracy_diff_se": acc_se,
                    "mean_accuracy_paired_t": mean(acc) / acc_se if acc_se > 0 else None,
                    "instances_better_mean_accuracy": sum(d > 0 for d in acc),
                    "instances_worse_mean_accuracy": sum(d < 0 for d in acc),
                })
        if se_sq > 0:
            entry["composite_paired_se"] = math.sqrt(se_sq)
            entry["composite_z"] = entry["composite_gain"] / math.sqrt(se_sq)
        summary["results"][name] = entry

    official = load(ROOT / "scoring" / "scores_test.json")
    if official:
        same = {}
        for exp, payload in official["experiments"].items():
            for method, metrics in payload["results"].items():
                other = attempts.get(method, {}).get(exp)
                same[f"{exp}:{method}"] = bool(other) and all(abs(metrics[k] - other[k]) < 1e-12 for k in metrics)
        summary["official_scores_equal_cohort_rerun"] = same
    for check in ("replaced_task",):
        a = attempts.get(f"{check}:bipartite")
        if a:
            summary[f"{check}_reference_unchanged"] = all(
                abs(a[e][m] - attempts[reference_name][e][m]) < 1e-12 for e in a for m in a[e]
            )

    train = load(OUT / "cohort_train" / "scores_train.json") or load(OUT / "cohort" / "scores_train.json")
    if train:
        summary["train_vs_test_mean_accuracy"] = {
            exp: {m: {"train": train["experiments"][exp]["results"][m]["mean_accuracy"],
                      "test": attempts[m][exp]["mean_accuracy"]}
                  for m in train["experiments"][exp]["results"] if m in attempts}
            for exp in train["experiments"]
        }
    summary["checks"] = records
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True))

    lines = ["| Attempt | digits mean acc | fried mean acc | composite gain | paired SE | z |",
             "|---|---:|---:|---:|---:|---:|"]
    for name, entry in sorted(summary["results"].items(), key=lambda kv: -kv[1]["composite_gain"]):
        d = entry["metrics"].get("digits_selection", {}).get("mean_accuracy", float("nan"))
        f = entry["metrics"].get("fried_selection", {}).get("mean_accuracy", float("nan"))
        se = entry.get("composite_paired_se")
        z = entry.get("composite_z")
        lines.append(f"| {name} | {d:.4f} | {f:.4f} | {entry['composite_gain']:+.3f} | "
                     f"{'' if se is None else f'{se:.3f}'} | {'' if z is None else f'{z:+.1f}'} |")
    lines += ["", "| Check | test exit | message |", "|---|---:|---|"]
    for name, record in records.items():
        lines.append(f"| {name} | {record.get('test_exit_code')} | {record.get('failure_message', '')[:150]} |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
