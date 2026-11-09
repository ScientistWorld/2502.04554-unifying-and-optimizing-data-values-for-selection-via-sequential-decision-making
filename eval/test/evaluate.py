"""Held-out (test-slice) evaluation of every registered ranker.

Self-contained on purpose: this module does not import ``data/``, ``method/``,
``baseline/`` or ``eval/train``. It draws its own held-out instances from the
same two generators the visible tasks use (scikit-learn digits; OpenML-style
binarized Friedman #1 "fried"), with seeds derived from a secret held only
here, so the instances cannot be regenerated from visible code.

Protocol, per run:
1. Build ``N_INSTANCES`` held-out instances per dataset. Test features and
   labels stay in this process; only the candidate pool and the validation
   set are written to a temporary directory (ranker contract in
   ``data/instances.py``).
2. Run every ranker in ``scripts/rankers/*.sh`` on that directory.
3. Require, for every ranker, exactly one ranking per instance that is a
   permutation of the instance's full candidate pool (JSON integers). Any
   missing, malformed, or partial output -- or a ranker that fails -- fails
   the whole evaluation with a non-zero exit status.
4. Retrain the fixed target learner on every prefix of each ranking and
   score the test-accuracy selection curve. Nothing a ranker writes besides
   the ranking is read.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import warnings
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sklearn.datasets import load_digits, make_friedman1
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
_SECRET = 0x6542EE03AEEADB28
DATASETS = ("digits", "fried")
DATASET_CODES = {"digits": 1, "fried": 2}
SPLIT_SIZES = {"digits": (100, 100, 1000), "fried": (50, 50, 500)}
FRIED_POOL = 5000
N_INSTANCES = 100
RANKER_TIMEOUT_SECONDS = 4 * 3600
SCORED_METRICS = (
    "mean_accuracy",
    "early10_accuracy",
    "early20_accuracy",
    "tail_accuracy",
    "max_accuracy_drop",
)


@dataclass(frozen=True)
class HeldOutInstance:
    dataset: str
    instance_id: str
    method_seed: int
    x_train: np.ndarray
    y_train: np.ndarray
    x_valid: np.ndarray
    y_valid: np.ndarray
    x_test: np.ndarray
    y_test: np.ndarray


# ----------------------------------------------------------------------------
# Held-out instance generation (same procedure as the visible provider).
# ----------------------------------------------------------------------------

def _generation_seed(dataset: str, index: int) -> int:
    sequence = np.random.SeedSequence([_SECRET, DATASET_CODES[dataset], index])
    return int(sequence.generate_state(1, dtype=np.uint32)[0])


def _balanced(x, y, size, rng):
    classes = np.unique(y)
    selected: list[int] = []
    per_class = max(1, size // len(classes))
    for cls in classes:
        idx = np.flatnonzero(y == cls)
        selected.extend(rng.choice(idx, min(per_class, len(idx)), replace=False).tolist())
    remaining = np.setdiff1d(np.arange(len(y)), np.array(selected))
    if len(selected) < size:
        selected.extend(rng.choice(remaining, size - len(selected), replace=False).tolist())
    selected = np.array(selected[:size])
    rng.shuffle(selected)
    return x[selected], y[selected]


def _raw(dataset: str, seed: int):
    if dataset == "digits":
        raw = load_digits()
        return raw.data.astype(np.float64) / 16.0, raw.target.astype(int)
    x, target = make_friedman1(n_samples=FRIED_POOL, n_features=10, noise=1.0, random_state=seed)
    return x.astype(np.float64), (target > target.mean()).astype(int)


def build_instance(dataset: str, index: int) -> HeldOutInstance:
    seed = _generation_seed(dataset, index)
    n_train, n_valid, n_test = SPLIT_SIZES[dataset]
    x, y = _raw(dataset, seed)
    rng = np.random.Generator(np.random.PCG64(seed))
    x_work, x_test, y_work, y_test = train_test_split(
        x, y, train_size=n_train + n_valid, test_size=n_test, random_state=seed, stratify=y
    )
    x_train, y_train = _balanced(x_work, y_work, n_train, rng)
    keep = np.ones(len(x_work), dtype=bool)
    for row, label in zip(x_train, y_train):
        hits = np.flatnonzero(keep & (y_work == label) & np.all(x_work == row, axis=1))
        if len(hits):
            keep[hits[0]] = False
    x_valid, y_valid = _balanced(x_work[keep], y_work[keep], n_valid, rng)
    scaler = StandardScaler().fit(np.vstack([x_train, x_valid]))
    return HeldOutInstance(
        dataset=dataset,
        instance_id=f"{dataset}_h{index:03d}",
        method_seed=1_000_000 + 1000 * DATASET_CODES[dataset] + index,
        x_train=scaler.transform(x_train),
        y_train=y_train.astype(int),
        x_valid=scaler.transform(x_valid),
        y_valid=y_valid.astype(int),
        x_test=scaler.transform(x_test),
        y_test=y_test.astype(int),
    )


def write_inputs(directory: Path, inst: HeldOutInstance) -> None:
    np.savez(
        directory / f"{inst.instance_id}.npz",
        x_train=inst.x_train.astype(np.float64),
        y_train=inst.y_train.astype(np.int64),
        x_valid=inst.x_valid.astype(np.float64),
        y_valid=inst.y_valid.astype(np.int64),
        dataset=np.array(inst.dataset),
        instance_id=np.array(inst.instance_id),
        seed=np.array(inst.method_seed, dtype=np.int64),
    )


# ----------------------------------------------------------------------------
# Fixed target learner and selection-curve metrics.
# ----------------------------------------------------------------------------

def _accuracy_after_training(x_fit, y_fit, x_eval, y_eval) -> float:
    classes = np.unique(y_fit)
    if len(classes) < 2:
        return float(np.mean(y_eval == classes[0]))
    model = LogisticRegression(C=1.0, solver="lbfgs", max_iter=500)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        model.fit(x_fit, y_fit)
    return float(accuracy_score(y_eval, model.predict(x_eval)))


def test_curve(inst: HeldOutInstance, ranking: list[int]) -> list[float]:
    order = np.asarray(ranking, dtype=int)
    return [
        _accuracy_after_training(inst.x_train[order[:k]], inst.y_train[order[:k]], inst.x_test, inst.y_test)
        for k in range(1, len(order) + 1)
    ]


def curve_summary(curve: list[float]) -> dict[str, float]:
    arr = np.asarray(curve, dtype=float)
    steps = np.diff(arr)
    return {
        "mean_accuracy": float(arr.mean()),
        "early10_accuracy": float(arr[:10].mean()),
        "early20_accuracy": float(arr[:20].mean()),
        "tail_accuracy": float(arr[20:].mean()),
        "max_accuracy_drop": float(max(0.0, float(-steps.min()))) if len(steps) else 0.0,
    }


# ----------------------------------------------------------------------------
# Rankers.
# ----------------------------------------------------------------------------

def checked_ranking(path: Path, n_train: int) -> list[int]:
    if not path.is_file():
        raise SystemExit(f"FAILED: no ranking written for held-out instance {path.stem}")
    try:
        payload = json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"FAILED: {path.name} is not valid JSON ({exc})")
    raw = payload.get("ranking") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        raise SystemExit(f"FAILED: {path.name} has no 'ranking' list")
    if len(raw) != n_train:
        raise SystemExit(f"FAILED: {path.name} ranks {len(raw)} points; the candidate pool has {n_train}")
    if any(isinstance(v, bool) or not isinstance(v, int) for v in raw):
        raise SystemExit(f"FAILED: {path.name} ranking entries must be JSON integers")
    if sorted(raw) != list(range(n_train)):
        raise SystemExit(f"FAILED: {path.name} ranking is not a permutation of the candidate pool")
    return list(raw)


def run_ranker(name: str, script: Path, inputs: Path, outputs: Path, timeout: float) -> None:
    outputs.mkdir(parents=True)
    print(f"[test] running ranker {name}", flush=True)
    try:
        proc = subprocess.run(
            ["bash", str(script.resolve()), str(inputs), str(outputs)], cwd=ROOT, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise SystemExit(f"FAILED: ranker {name} exceeded {timeout:.0f} s")
    if proc.returncode != 0:
        raise SystemExit(f"FAILED: ranker {name} exited with status {proc.returncode}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--rankers-dir", default="scripts/rankers")
    parser.add_argument("--scores", default="scoring/scores_test.json")
    parser.add_argument(
        "--curves-dir",
        default=None,
        help="optional directory for per-instance curves (diagnostics only; keep it out of git, "
        "since per-instance held-out curves are test feedback)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out = Path(args.scores)
    # A failed run must never leave a scores file behind (stale or forged).
    out.unlink(missing_ok=True)
    try:
        evaluate(args, out)
    except BaseException:
        out.unlink(missing_ok=True)
        raise


def evaluate(args: argparse.Namespace, out: Path) -> None:
    rankers_dir = Path(args.rankers_dir)
    if not rankers_dir.is_absolute():
        rankers_dir = ROOT / rankers_dir
    rankers = {p.stem: p for p in sorted(rankers_dir.glob("*.sh"))}
    if not rankers:
        raise SystemExit(f"FAILED: no rankers (*.sh) found in {rankers_dir}")

    instances = [build_instance(ds, i) for ds in DATASETS for i in range(N_INSTANCES)]
    rankings: dict[str, dict[str, list[int]]] = {}
    with tempfile.TemporaryDirectory(prefix="heldout_") as tmp:
        inputs = Path(tmp) / "instances"
        inputs.mkdir()
        for inst in instances:
            write_inputs(inputs, inst)
        for name, script in rankers.items():
            outputs = Path(tmp) / "outputs" / name
            run_ranker(name, script, inputs, outputs, RANKER_TIMEOUT_SECONDS)
            rankings[name] = {
                inst.instance_id: checked_ranking(outputs / f"{inst.instance_id}.json", len(inst.y_train))
                for inst in instances
            }
        shutil.rmtree(inputs, ignore_errors=True)

    curves_dir = Path(args.curves_dir) if args.curves_dir else None
    if curves_dir is not None:
        curves_dir.mkdir(parents=True, exist_ok=True)
        for stale in curves_dir.glob("*.json"):
            stale.unlink()

    scores: dict = {"experiments": {}}
    for name in rankers:
        rows: dict[str, list[dict]] = defaultdict(list)
        pooled: dict[str, list[float]] = defaultdict(list)
        records = []
        for inst in instances:
            curve = test_curve(inst, rankings[name][inst.instance_id])
            summary = curve_summary(curve)
            rows[inst.dataset].append(summary)
            pooled[inst.dataset].extend(curve)
            records.append({"instance_id": inst.instance_id, "dataset": inst.dataset, "summary": summary, "curve": curve})
        for dataset in DATASETS:
            result = {key: float(np.mean([r[key] for r in rows[dataset]])) for key in SCORED_METRICS}
            result["curve_accuracy_std"] = float(np.std(pooled[dataset]))
            for key, value in result.items():
                if not np.isfinite(value):
                    raise SystemExit(f"FAILED: non-finite {key} for {name} on {dataset}")
            scores["experiments"].setdefault(f"{dataset}_selection", {"results": {}})["results"][name] = result
        if curves_dir is not None:
            (curves_dir / f"{name}.json").write_text(
                json.dumps({"slice": "test", "method": name, "instances": records})
            )
        print(f"[test] scored {name}", flush=True)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scores, indent=2, sort_keys=True))
    print(f"[test] wrote {out} ({N_INSTANCES} held-out instances per dataset)", file=sys.stderr)


if __name__ == "__main__":
    main()
