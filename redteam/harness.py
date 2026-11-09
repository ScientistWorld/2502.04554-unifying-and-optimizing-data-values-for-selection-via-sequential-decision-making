"""Install one audit method, score it with pristine evaluators, restore files."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "redteam/_state"
MUTATED = (
    "data/tasks.py", "checkpoints/rankings", "scoring/scores_train.json",
    "scoring/scores_test.json", "scoring/curves_train", "scoring/curves_test",
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def backup():
    if (STATE / "manifest.json").exists():
        return
    STATE.mkdir(parents=True, exist_ok=True)
    exists = {}
    for relative in MUTATED:
        source, target = ROOT / relative, STATE / relative
        exists[relative] = source.exists()
        if source.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
    (STATE / "manifest.json").write_text(json.dumps(exists, indent=2))
    shutil.copy2(ROOT / "scoring/scores_test.json", ROOT / "redteam/stored_reference_scores_test.json")


def restore():
    exists = json.loads((STATE / "manifest.json").read_text())
    for relative, present in exists.items():
        target, source = ROOT / relative, STATE / relative
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()
        if present:
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
    # Eliminate timestamp-dependent bytecode reuse after changing the data file.
    # No interpreter hooks, package installs, or environment changes are used.
    for path in (ROOT / "data/__pycache__").glob("tasks.*.pyc"):
        path.unlink()


def install_replaced_task_shortcut():
    source = ROOT / "data/tasks.py"
    source.write_text(source.read_text() + '''

# SHORTCUT: replace the fixed data task with labels encoded in input features.
# This deliberately changes only the scientist-visible data provider, to test
# whether the hidden evaluation independently fixes the task definition.
_shortcut_original_loader = load_task


def load_task(name, seed, train_size=None):
    from dataclasses import replace
    task = _shortcut_original_loader(name, seed, train_size=train_size)
    classes = int(max(task.y_train.max(), task.y_valid.max(), task.y_test.max())) + 1
    basis = np.eye(classes, dtype=float)
    return replace(task, x_train=basis[task.y_train],
                   x_valid=basis[task.y_valid], x_test=basis[task.y_test])
''')


def run(name):
    backup()
    restore()
    folder = ROOT / "redteam" / name
    folder.mkdir(parents=True, exist_ok=True)
    evaluator_paths = [ROOT / "scripts/evaluate_test.sh", ROOT / "eval/test/evaluate.py",
                       ROOT / "data/metrics.py"]
    original_hashes = {str(p.relative_to(ROOT)): digest(p) for p in evaluator_paths}
    record = {"name": name, "test_command": ["bash", "scripts/evaluate_test.sh"],
              "test_arguments": [], "evaluator_sha256_before": original_hashes}
    for relative in MUTATED[1:]:
        path = ROOT / relative
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    (ROOT / "checkpoints/rankings").mkdir(parents=True)
    start = time.monotonic()
    try:
        if name == "shortcut_replaced_task":
            install_replaced_task_shortcut()
        with (folder / "run.log").open("w") as log:
            subprocess.run([sys.executable, "-m", "redteam.generate", name], cwd=ROOT,
                           stdout=log, stderr=subprocess.STDOUT, check=True)
            # Scores and trained ranking artifacts are intentionally persistent,
            # exactly what survives a fresh-container evaluation.
            shutil.copytree(ROOT / "checkpoints/rankings", folder / "rankings", dirs_exist_ok=True)
            if name == "reference_seed0":
                for path in (folder / "rankings").glob("*.json"):
                    payload = json.loads(path.read_text())
                    stable = folder / "rankings" / f"bipartite_{payload['dataset']}_seed{payload['seed']}.json"
                    if stable != path:
                        stable.write_text(json.dumps(payload, indent=2))
            train = subprocess.run(["bash", "scripts/evaluate_train.sh"], cwd=ROOT,
                                   stdout=log, stderr=subprocess.STDOUT)
            record["train_exit_code"] = train.returncode
            if name == "shortcut_forged_fields":
                fake = {"experiments": {dataset + "_selection": {"results": {
                    "bipartite": {"mean_accuracy": 1.0, "mean_accuracy_std": 0.0,
                                  "early10_accuracy": 1.0, "early20_accuracy": 1.0,
                                  "tail_accuracy": 1.0, "worst_prefix_accuracy": 1.0,
                                  "max_accuracy_drop": 0.0, "early_label_balance": 1.0}
                }} for dataset in ("digits", "synthetic_planes")}}
                (ROOT / "scoring/scores_test.json").write_text(json.dumps(fake, indent=2))
                (folder / "shortcut_forged_scores.json").write_text(json.dumps(fake, indent=2))
            # Always run the hidden test, including after an invalid train ranking.
            # This is a new interpreter; the method process has already exited.
            test_start = time.monotonic()
            test = subprocess.run(["bash", "scripts/evaluate_test.sh"], cwd=ROOT,
                                  stdout=log, stderr=subprocess.STDOUT)
            record["test_exit_code"] = test.returncode
            record["test_seconds"] = time.monotonic() - test_start
        for basename in ("scores_train.json", "scores_test.json"):
            path = ROOT / "scoring" / basename
            if path.exists():
                shutil.copy2(path, folder / basename)
        for basename in ("curves_train", "curves_test"):
            path = ROOT / "scoring" / basename
            if path.exists():
                shutil.copytree(path, folder / basename, dirs_exist_ok=True)
        if record["test_exit_code"] != 0:
            record["test_error_tail"] = (folder / "run.log").read_text()[-4000:]
    except Exception as exc:
        record["harness_error"] = repr(exc)
        raise
    finally:
        record["seconds"] = time.monotonic() - start
        record["evaluator_sha256_after"] = {
            str(p.relative_to(ROOT)): digest(p) for p in evaluator_paths}
        record["evaluator_unchanged"] = record["evaluator_sha256_after"] == original_hashes
        (folder / "run_record.json").write_text(json.dumps(record, indent=2))
        restore()
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("name")
    run(parser.parse_args().name)
