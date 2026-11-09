"""Variant and shortcut rankers used to check the hardened gym.

Every entry follows the normal ranker contract (data/instances.py):
``python -m redteam.hardening.variants NAME --instances DIR --output-dir DIR``.
Nothing here reads eval/test/, scoring/, or the paper. Honest variants use only
the instance inputs (candidate pool + validation set). Shortcuts are labelled.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from data.instances import iter_instances, write_ranking
from data.metrics import fit_eval_logreg
from data.tasks import load_task
from method.bipartite_selection import greedy_maximum_coverage, learn_bipartite_edges, rank_instance


# ----------------------------------------------------------------------------
# Honest variants (better / weaker / higher-compute alternatives).
# ----------------------------------------------------------------------------

def coverage_reset(inst):
    """Reference graph; once every validation point is covered, reset coverage."""
    n = len(inst["y_train"])
    edges, _ = learn_bipartite_edges(
        inst["x_train"], inst["y_train"], inst["x_valid"], inst["y_valid"],
        seed=inst["seed"], subset_samples=80, subset_size=max(2, min(n // 5, 20)), n_thresholds=25,
    )
    remaining = set(range(n))
    uncovered = np.ones(edges.shape[1], dtype=bool)
    ranking = []
    while remaining:
        gains = {i: int(np.sum(edges[i] & uncovered)) for i in remaining}
        if max(gains.values()) == 0:
            uncovered[:] = True
            gains = {i: int(np.sum(edges[i] & uncovered)) for i in remaining}
        best = max(remaining, key=lambda i: (gains[i], -i))
        ranking.append(best)
        uncovered &= ~edges[best]
        remaining.remove(best)
    return ranking


def validation_prototypes(inst):
    """Class prototypes nearest the validation class centroids, class order by utility."""
    x_train, y_train = inst["x_train"], inst["y_train"]
    x_valid, y_valid = inst["x_valid"], inst["y_valid"]
    queues = {}
    for label in np.unique(y_train):
        idx = np.flatnonzero(y_train == label)
        center = x_valid[y_valid == label].mean(axis=0) if np.any(y_valid == label) else x_train[idx].mean(axis=0)
        dist = ((x_train[idx] - center) ** 2).sum(axis=1)
        queues[int(label)] = idx[np.argsort(dist, kind="stable")].tolist()
    remaining_labels = set(queues)
    ranking, class_order = [], []
    while remaining_labels:
        utilities = {}
        for label in sorted(remaining_labels):
            chosen = ranking + [queues[label][0]]
            utilities[label] = fit_eval_logreg(
                x_train[chosen], y_train[chosen], x_valid, y_valid, inst["seed"] + len(chosen)
            )
        label = max(sorted(remaining_labels), key=lambda c: utilities[c])
        ranking.append(queues[label].pop(0))
        class_order.append(label)
        remaining_labels.remove(label)
    while any(queues.values()):
        for label in class_order:
            if queues[label]:
                ranking.append(queues[label].pop(0))
    return ranking


def label_blocks(inst):
    """Weaker: all points of one class, then the next class, ..."""
    return np.argsort(inst["y_train"], kind="stable").tolist()


def brute_force_greedy(inst, x_eval=None, y_eval=None):
    """Enumerate every remaining candidate at every step (n(n+1)/2 retrainings)."""
    x_train, y_train = inst["x_train"], inst["y_train"]
    x_eval = inst["x_valid"] if x_eval is None else x_eval
    y_eval = inst["y_valid"] if y_eval is None else y_eval
    classes = np.unique(y_train)
    ranking, remaining = [], set(range(len(y_train)))
    while remaining:
        utilities = {}
        for i in sorted(remaining):
            chosen = ranking + [i]
            utilities[i] = fit_eval_logreg(x_train[chosen], y_train[chosen], x_eval, y_eval, inst["seed"] + len(chosen))
        counts = {c: int(np.sum(y_train[ranking] == c)) for c in classes}
        best = max(sorted(remaining), key=lambda i: (utilities[i], -counts[y_train[i]], -i))
        ranking.append(best)
        remaining.remove(best)
    return ranking


def budgeted_greedy(inst, budget=1000):
    """Validation-utility greedy within the 1000-retraining budget: at each step
    evaluate at most budget // n randomly drawn remaining candidates."""
    x_train, y_train = inst["x_train"], inst["y_train"]
    n = len(y_train)
    per_step = max(1, budget // n)
    rng = np.random.default_rng(inst["seed"])
    classes = np.unique(y_train)
    ranking, remaining, fits = [], list(range(n)), 0
    while remaining:
        if len(remaining) == 1:
            ranking.append(remaining.pop())
            break
        pool = remaining if len(remaining) <= per_step else rng.choice(remaining, per_step, replace=False).tolist()
        utilities = {}
        for i in pool:
            chosen = ranking + [int(i)]
            utilities[int(i)] = fit_eval_logreg(
                x_train[chosen], y_train[chosen], inst["x_valid"], inst["y_valid"], inst["seed"] + len(chosen)
            )
            fits += 1
        counts = {c: int(np.sum(y_train[ranking] == c)) for c in classes}
        best = max(sorted(utilities), key=lambda i: (utilities[i], -counts[y_train[i]], -i))
        ranking.append(best)
        remaining.remove(best)
    assert fits <= budget, fits
    return ranking


def more_samples_800(inst):
    """Reference method with 10x the sampled-subset utility evaluations."""
    return rank_instance(inst, subset_samples=800)[0]


def reference(inst):
    return rank_instance(inst)[0]


# ----------------------------------------------------------------------------
# Shortcuts.
# ----------------------------------------------------------------------------

_FINGERPRINTS: dict[str, dict[bytes, int]] = {}


def _fingerprint(x_train: np.ndarray) -> bytes:
    return np.round(np.sort(x_train, axis=0)[:3], 6).tobytes()


def rebuilt_answers(inst):
    """SHORTCUT: find the visible seed that regenerates this instance and use its
    test labels for greedy selection. Falls back to the reference ranking."""
    dataset = inst["dataset"]
    if dataset not in _FINGERPRINTS:
        table = {}
        for seed in range(0, 2001):
            table[_fingerprint(load_task(dataset, seed).x_train)] = seed
        _FINGERPRINTS[dataset] = table
    candidates = [inst["seed"]]
    match = _FINGERPRINTS[dataset].get(_fingerprint(inst["x_train"]))
    if match is not None:
        candidates.insert(0, match)
    for seed in candidates:
        try:
            task = load_task(dataset, int(seed))
        except Exception:
            continue
        if task.x_train.shape == inst["x_train"].shape and np.allclose(task.x_train, inst["x_train"]):
            REBUILT_STATS["matched"] += 1
            return brute_force_greedy(inst, task.x_test, task.y_test)
    REBUILT_STATS["unmatched"] += 1
    return reference(inst)


REBUILT_STATS = {"matched": 0, "unmatched": 0}


def round_robin(inst):
    """SHORTCUT companion for the replaced-task check: class-interleaved order."""
    y = inst["y_train"]
    queues = {int(c): np.flatnonzero(y == c).tolist() for c in np.unique(y)}
    ranking = []
    while any(queues.values()):
        for c in sorted(queues):
            if queues[c]:
                ranking.append(queues[c].pop(0))
    return ranking


SCORED = {
    "reference": reference,
    "coverage_reset": coverage_reset,
    "validation_prototypes": validation_prototypes,
    "label_blocks": label_blocks,
    "brute_force_greedy": brute_force_greedy,
    "more_samples_800": more_samples_800,
    "budgeted_greedy": budgeted_greedy,
    "rebuilt_answers": rebuilt_answers,
    "round_robin": round_robin,
}


def _raw_write(output_dir: Path, inst_id: str, text: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{inst_id}.json").write_text(text)


def run_special(name: str, instances: list[dict], output_dir: Path) -> None:
    """Shortcuts that manipulate the output files rather than the ranking logic."""
    first_by_dataset: dict[str, list[int]] = {}
    for index, inst in enumerate(instances):
        n = len(inst["y_train"])
        inst_id = inst["instance_id"]
        if name == "larger_pool":
            write_ranking(output_dir, inst_id, list(range(n + 500)), train_size=n + 500)
        elif name == "skip_half":
            if index % 2 == 0:
                write_ranking(output_dir, inst_id, reference(inst))
        elif name == "copied_ranking":
            if inst["dataset"] not in first_by_dataset:
                first_by_dataset[inst["dataset"]] = reference(inst)
            write_ranking(output_dir, inst_id, first_by_dataset[inst["dataset"]], repeat_of="first instance")
        elif name == "forged_fields":
            ranking = np.random.default_rng(inst["seed"]).permutation(n).tolist()
            write_ranking(
                output_dir, inst_id, ranking,
                mean_accuracy=1.0, curve=[1.0] * n, success=True, verified=True,
                utility_queries=0, runtime_seconds=-1, score=1e9, failure=None,
            )
        elif name == "invalid_empty":
            _raw_write(output_dir, inst_id, json.dumps({"ranking": []}))
        elif name == "invalid_duplicate":
            _raw_write(output_dir, inst_id, json.dumps({"ranking": [0] * n}))
        elif name == "invalid_nan":
            _raw_write(output_dir, inst_id, json.dumps({"ranking": [math.nan] + list(range(1, n))}))
        elif name == "invalid_float":
            _raw_write(output_dir, inst_id, json.dumps({"ranking": [float(i) for i in range(n)]}))
        elif name == "singleton":
            _raw_write(output_dir, inst_id, json.dumps({"ranking": [0]}))
        else:
            raise ValueError(name)
    if name == "forged_fields":
        perfect = {"mean_accuracy": 1.0, "early10_accuracy": 1.0, "early20_accuracy": 1.0,
                   "tail_accuracy": 1.0, "max_accuracy_drop": 0.0, "curve_accuracy_std": 0.0}
        forged = {"experiments": {f"{d}_selection": {"results": {"forged_fields": perfect}}
                                  for d in ("digits", "fried")}}
        Path("scoring").mkdir(exist_ok=True)
        Path("scoring/scores_test.json").write_text(json.dumps(forged))


SPECIAL = {
    "larger_pool", "skip_half", "copied_ranking", "forged_fields", "invalid_empty",
    "invalid_duplicate", "invalid_nan", "invalid_float", "singleton",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("name", choices=sorted(set(SCORED) | SPECIAL))
    parser.add_argument("--instances", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    instances = list(iter_instances(args.instances))
    if args.name in SPECIAL:
        run_special(args.name, instances, output_dir)
        return
    fn = SCORED[args.name]
    for inst in instances:
        write_ranking(output_dir, inst["instance_id"], fn(inst), method=args.name)
    if args.name == "rebuilt_answers":
        print(f"rebuilt_answers: {json.dumps(REBUILT_STATS)}", flush=True)
        (output_dir / "_rebuilt_stats.json").write_text(json.dumps(REBUILT_STATS))


if __name__ == "__main__":
    main()
