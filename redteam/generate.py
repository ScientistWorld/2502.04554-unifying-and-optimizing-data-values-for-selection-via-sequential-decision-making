"""Visible-information-only methods and explicitly labelled shortcuts.

This file never reads eval/test, scoring/reference.json, or stored test scores.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from data.metrics import fit_eval_logreg, selection_curve
from data.tasks import load_task
from method.bipartite_selection import learn_bipartite_edges, greedy_maximum_coverage


DATASETS = ("digits", "synthetic_planes")
# This full seed schedule is present in the visible scripts/baseline.sh.
SEEDS = tuple(range(1, 21))


def reference(task, seed, offset=0, samples=80, reset=False):
    edges, graph = learn_bipartite_edges(
        task.x_train, task.y_train, task.x_valid, task.y_valid,
        seed=seed + offset, subset_samples=samples,
        subset_size=max(2, min(len(task.x_train) // 5, 20)), n_thresholds=25,
    )
    if not reset:
        ranking, gains = greedy_maximum_coverage(edges)
    else:
        remaining = set(range(len(task.y_train)))
        uncovered = np.ones(len(task.y_valid), dtype=bool)
        ranking, gains = [], []
        while remaining:
            gains_now = {i: int(np.sum(edges[i] & uncovered)) for i in remaining}
            if max(gains_now.values()) == 0:
                uncovered[:] = True
                gains_now = {i: int(np.sum(edges[i] & uncovered)) for i in remaining}
            best = max(remaining, key=lambda i: (gains_now[i], -i))
            ranking.append(best)
            gains.append(gains_now[best])
            uncovered &= ~edges[best]
            remaining.remove(best)
    return ranking, {"graph": graph, "coverage_gains": gains, "utility_queries": samples}


def prototypes(task, seed):
    """Representative examples, a distinct class each step, validation tie choice.

    The first pass uses at most C(C+1)/2 utility queries (55 for digits,
    three for the binary task), below the reference's 80 utility calls.
    Remaining points are ordered by proximity to validation class centroids,
    interleaving classes. No held-out information is consulted.
    """
    queues = {}
    for label in np.unique(task.y_train):
        indices = np.flatnonzero(task.y_train == label)
        center = task.x_valid[task.y_valid == label].mean(axis=0)
        distance = ((task.x_train[indices] - center) ** 2).sum(axis=1)
        queues[int(label)] = indices[np.argsort(distance, kind="stable")].tolist()
    remaining_labels = set(queues)
    ranking, class_order, queries = [], [], 0
    while remaining_labels:
        utilities = {}
        for label in sorted(remaining_labels):
            indices = ranking + [queues[label][0]]
            utilities[label] = fit_eval_logreg(
                task.x_train[indices], task.y_train[indices],
                task.x_valid, task.y_valid, seed + len(indices),
            )
            queries += 1
        label = max(sorted(remaining_labels), key=lambda c: utilities[c])
        ranking.append(queues[label].pop(0))
        class_order.append(label)
        remaining_labels.remove(label)
    while any(queues.values()):
        for label in class_order:
            if queues[label]:
                ranking.append(queues[label].pop(0))
    return ranking, {"utility_queries": queries}


def brute_force_shortcut(task, seed, oracle=False):
    """Shortcut: enumerate all next candidates, exceeding the reference budget.

    oracle=True is additionally a test-answer-reconstruction shortcut: the
    visible deterministic loader directly returns the complete test labels.
    """
    x_eval = task.x_test if oracle else task.x_valid
    y_eval = task.y_test if oracle else task.y_valid
    ranking, remaining, queries = [], set(range(len(task.y_train))), 0
    classes = np.unique(task.y_train)
    while remaining:
        utilities = {}
        for i in sorted(remaining):
            chosen = ranking + [i]
            utilities[i] = fit_eval_logreg(
                task.x_train[chosen], task.y_train[chosen], x_eval, y_eval,
                seed + len(chosen),
            )
            queries += 1
        counts = {c: int(np.sum(task.y_train[ranking] == c)) for c in classes}
        best = max(sorted(remaining), key=lambda i: (
            utilities[i], -counts[task.y_train[i]], -i,
        ))
        ranking.append(best)
        remaining.remove(best)
    return ranking, {"utility_queries": queries, "shortcut_test_labels": oracle}


def round_robin(task):
    queues = {int(c): np.flatnonzero(task.y_train == c).tolist()
              for c in np.unique(task.y_train)}
    ranking = []
    while any(queues.values()):
        for c in sorted(queues):
            if queues[c]:
                ranking.append(queues[c].pop(0))
    return ranking


def cached_reference(dataset, seed, out):
    path = Path("redteam/reference_seed0/rankings") / f"bipartite_{dataset}_seed{seed}.json"
    if not path.exists():
        raise RuntimeError("Run redteam/reference_seed0/run.sh first to build the reference cache")
    payload = json.loads(path.read_text())
    return payload["ranking"], payload.get("audit_metadata", {})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    args = parser.parse_args()
    name = args.name
    out = Path("checkpoints/rankings")
    out.mkdir(parents=True, exist_ok=True)
    records = []
    start = time.monotonic()
    for dataset in DATASETS:
        seed_payloads = []
        for seed in SEEDS:
            train_size = None
            if name == "shortcut_larger_pool":
                train_size = 600 if dataset == "digits" else 2000
            task = load_task(dataset, seed, train_size=train_size)
            metadata = {}
            if name.startswith("reference_seed"):
                offset = int(name.removeprefix("reference_seed")) * 1000
                ranking, metadata = reference(task, seed, offset=offset)
            elif name == "shortcut_more_samples":
                ranking, metadata = reference(task, seed, samples=800)
            elif name == "better_coverage_reset":
                ranking, metadata = reference(task, seed, reset=True)
            elif name == "better_validation_prototypes":
                ranking, metadata = prototypes(task, seed)
            elif name in {"weaker_random", "shortcut_forged_fields"}:
                ranking = np.random.default_rng(seed).permutation(len(task.y_train)).tolist()
            elif name == "weaker_label_blocks":
                ranking = np.argsort(task.y_train, kind="stable").tolist()
            elif name in {"shortcut_brute_force", "shortcut_rebuilt_answers"}:
                ranking, metadata = brute_force_shortcut(
                    task, seed, oracle=name == "shortcut_rebuilt_answers",
                )
            elif name == "shortcut_larger_pool":
                ranking, metadata = reference(task, seed)
            elif name == "shortcut_replaced_task":
                ranking = round_robin(task)
            elif name == "shortcut_singleton_constant":
                task = load_task(dataset, seed, train_size=1)
                ranking = [0]
            elif name == "shortcut_seed_cherry_pick":
                ranking, metadata = cached_reference(dataset, seed, out)
                # A shortcut, not tuning: intentionally use publicly rebuildable
                # test labels to select which scheduled test seeds to submit.
                metadata["shortcut_test_mean"] = float(np.mean(selection_curve(task, ranking, seed)))
            elif name.startswith("shortcut_invalid_"):
                if name == "shortcut_invalid_empty":
                    ranking = []
                elif name == "shortcut_invalid_constant":
                    ranking = [0] * len(task.y_train)
                elif name == "shortcut_invalid_impossible":
                    ranking = [float("nan")] + list(range(1, len(task.y_train)))
                else:
                    raise ValueError(name)
            else:
                raise ValueError(name)
            payload = {
                "method": "bipartite", "dataset": dataset, "seed": seed,
                "train_size": len(task.y_train), "valid_size": len(task.y_valid),
                "test_size": len(task.y_test), "ranking": ranking,
                "audit_metadata": metadata,
            }
            if name == "shortcut_forged_fields":
                payload.update({
                    "mean_accuracy": 1.0, "mean_accuracy_std": 0.0,
                    "curve": [1.0] * len(ranking), "success": True,
                    "verified": True, "selection_budget": 0,
                    "runtime_seconds": -1000000000, "score": float("inf"),
                    "utility_queries": 0, "failure": None,
                })
            seed_payloads.append(payload)
            print(f"{name}: {dataset} seed={seed} queries={metadata.get('utility_queries', 0)}", flush=True)
        if name == "shortcut_seed_cherry_pick":
            # Train evaluator exposes seeds 1..10; visible baseline schedule is
            # 1..20. Keep the train half; submit ten copies of the best other
            # scheduled seed under different filenames, faking stable repeats.
            train_seeds = set(range(1, 11))
            eligible = [p for p in seed_payloads if p["seed"] not in train_seeds]
            best = max(eligible, key=lambda p: p["audit_metadata"]["shortcut_test_mean"])
            seed_payloads = [p for p in seed_payloads if p["seed"] in train_seeds]
            for repeat in range(10):
                duplicate = dict(best)
                duplicate["shortcut_repeat"] = repeat
                seed_payloads.append(duplicate)
        for index, payload in enumerate(seed_payloads):
            path = out / f"bipartite_{dataset}_seed{payload['seed']}_row{index}.json"
            path.write_text(json.dumps(payload, indent=2))
            # Give the reference cache stable public filenames too.
            records.append({"dataset": dataset, "seed": payload["seed"],
                            "utility_queries": payload["audit_metadata"].get("utility_queries", 0),
                            "train_size": payload["train_size"]})
    result = {"name": name, "generation_seconds": time.monotonic() - start, "runs": records}
    Path(f"redteam/{name}/generation.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
