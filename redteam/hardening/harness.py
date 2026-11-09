"""Run the hardening checks through the real evaluators.

Each check registers its rankers in a private rankers directory and calls
``bash scripts/evaluate_test.sh`` (and, for the honest cohort, also
``scripts/evaluate_train.sh``) -- the same code path as the hidden test.
Aggregate scores and logs go to ``redteam/hardening/<check>/``; per-instance
held-out curves (test feedback) go only to the gitignored ``tmp/hardening/``.

Usage: python -m redteam.hardening.harness [--force] [CHECK ...]
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "redteam" / "hardening"
TMP = ROOT / "tmp" / "hardening"

REGISTERED = ("bipartite", "random", "loo", "datashap")
COHORT = REGISTERED + (
    "coverage_reset", "validation_prototypes", "label_blocks", "brute_force_greedy", "more_samples_800",
)
CHECKS = {
    "cohort": {"rankers": COHORT, "train": True},
    # Visible-slice rerun after the method-seed decoupling (test side unchanged).
    "cohort_train": {"rankers": COHORT, "train": True, "train_only": True},
    "budgeted_greedy": {"rankers": ("budgeted_greedy",)},
    "rebuilt_answers": {"rankers": ("rebuilt_answers",)},
    "replaced_task": {"rankers": ("round_robin", "bipartite"), "patch_tasks": True},
    "larger_pool": {"rankers": ("larger_pool",)},
    "skip_half": {"rankers": ("skip_half",)},
    "copied_ranking": {"rankers": ("copied_ranking",)},
    "forged_fields": {"rankers": ("forged_fields",), "default_scores_path": True},
    "invalid_empty": {"rankers": ("invalid_empty",)},
    "invalid_duplicate": {"rankers": ("invalid_duplicate",)},
    "invalid_nan": {"rankers": ("invalid_nan",)},
    "invalid_float": {"rankers": ("invalid_float",)},
    "singleton": {"rankers": ("singleton",)},
}

ONE_HOT_PATCH = '''

# HARDENING CHECK (temporary): replace the visible task with label-encoding
# one-hot features, as the earlier red-team "replaced task" shortcut did.
_hardening_original_loader = load_task


def load_task(name, seed):
    from dataclasses import replace
    task = _hardening_original_loader(name, seed)
    classes = int(max(task.y_train.max(), task.y_valid.max(), task.y_test.max())) + 1
    basis = np.eye(classes, dtype=float)
    return replace(task, x_train=basis[task.y_train], x_valid=basis[task.y_valid], x_test=basis[task.y_test])
'''


def write_rankers(directory: Path, names) -> None:
    if directory.exists():
        shutil.rmtree(directory)
    directory.mkdir(parents=True)
    for name in names:
        if name in REGISTERED:
            body = f'exec bash "{ROOT}/scripts/rankers/{name}.sh" "$1" "$2"'
        else:
            body = f'cd "{ROOT}"\nexec python -m redteam.hardening.variants {name} --instances "$1" --output-dir "$2"'
        (directory / f"{name}.sh").write_text(f"#!/bin/bash\nset -euo pipefail\n{body}\n")


def run(cmd: list[str], log_path: Path) -> tuple[int, float]:
    start = time.monotonic()
    with log_path.open("a") as log:
        log.write(f"$ {' '.join(cmd)}\n")
        log.flush()
        proc = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    return proc.returncode, time.monotonic() - start


def run_check(name: str, spec: dict, force: bool) -> dict:
    folder = OUT / name
    record_path = folder / "record.json"
    if record_path.exists() and not force:
        print(f"[harness] {name}: cached", flush=True)
        return json.loads(record_path.read_text())
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    work = TMP / name
    if work.exists():
        shutil.rmtree(work)
    rankers_dir = work / "rankers"
    write_rankers(rankers_dir, spec["rankers"])
    log_path = folder / "run.log"
    record = {"check": name, "rankers": list(spec["rankers"])}

    tasks_file = ROOT / "data" / "tasks.py"
    original_tasks = tasks_file.read_text()
    official = ROOT / "scoring" / "scores_test.json"
    official_backup = official.read_bytes() if official.exists() else None
    try:
        if spec.get("patch_tasks"):
            tasks_file.write_text(original_tasks + ONE_HOT_PATCH)
            record["patched_data_tasks"] = True
        if spec.get("default_scores_path"):
            scores_path = ROOT / "scoring" / "scores_test.json"
            scores_arg: list[str] = []
        else:
            scores_path = folder / "scores_test.json"
            scores_arg = ["--scores", str(scores_path)]
        if spec.get("train_only"):
            record.update({"test_exit_code": 0, "test_seconds": 0.0, "scores_file_exists": False})
        else:
            cmd = ["bash", "scripts/evaluate_test.sh", "--rankers-dir", str(rankers_dir),
                   *scores_arg, "--curves-dir", str(work / "curves_test")]
            code, seconds = run(cmd, log_path)
            record.update({"test_exit_code": code, "test_seconds": seconds,
                           "scores_file_exists": scores_path.exists()})
        if scores_path.exists() and scores_path != folder / "scores_test.json":
            shutil.copy2(scores_path, folder / "scores_test.json")
            scores_path.unlink()
        if spec.get("train"):
            cmd = ["bash", "scripts/evaluate_train.sh", "--rankers-dir", str(rankers_dir),
                   "--scores", str(folder / "scores_train.json"),
                   "--curves-dir", str(work / "curves_train"),
                   "--instances-dir", str(work / "instances_train"),
                   "--rankings-dir", str(work / "rankings_train")]
            code, seconds = run(cmd, log_path)
            record.update({"train_exit_code": code, "train_seconds": seconds})
    finally:
        tasks_file.write_text(original_tasks)
        if spec.get("default_scores_path"):
            if official_backup is not None:
                official.write_bytes(official_backup)
            elif official.exists():
                official.unlink()
        for pyc in (ROOT / "data" / "__pycache__").glob("tasks.*.pyc"):
            pyc.unlink()
    if record["test_exit_code"] != 0:
        lines = log_path.read_text().splitlines()
        record["failure_message"] = next((l for l in reversed(lines) if "FAILED" in l), lines[-1] if lines else "")
    record_path.write_text(json.dumps(record, indent=2))
    print(f"[harness] {name}: test exit {record['test_exit_code']}", flush=True)
    return record


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checks", nargs="*", default=list(CHECKS))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    for name in args.checks:
        try:
            run_check(name, CHECKS[name], args.force)
        except Exception as exc:  # keep going; record the harness error
            (OUT / name).mkdir(parents=True, exist_ok=True)
            (OUT / name / "harness_error.txt").write_text(repr(exc))
            print(f"[harness] {name}: harness error {exc!r}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
