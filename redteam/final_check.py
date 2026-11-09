"""Lightweight audit-evidence and restoration checks; no model computation."""
from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AUDIT = ROOT / "redteam"


def file_hashes(path):
    if not path.exists():
        return None
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return {str(p.relative_to(path)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(path.rglob("*")) if p.is_file()}


def main():
    records = [json.loads(p.read_text()) for p in AUDIT.glob("*/run_record.json")]
    assert len(records) == 18
    assert sum(r["test_exit_code"] == 0 for r in records) == 15
    assert all(r["test_command"] == ["bash", "scripts/evaluate_test.sh"] and
               r["test_arguments"] == [] and r["evaluator_unchanged"] and
               "harness_error" not in r for r in records)
    for record in records:
        folder = AUDIT / record["name"]
        assert (folder / "run.sh").is_file()
        if record["test_exit_code"] == 0:
            assert (folder / "scores_test.json").is_file()
            assert (folder / "test_trials.json").is_file()
        else:
            assert record["test_error_tail"]
            assert not (folder / "scores_test.json").exists()
    summary = json.loads((AUDIT / "summary.json").read_text())
    assert summary["all_evaluators_unchanged"]
    assert summary["reference_rank_spread"]["range"] == 0
    ranks = summary["scores"]
    assert all(ranks[name] > 0 for name in
               ("better_coverage_reset", "better_validation_prototypes"))
    assert all(ranks[name] < 0 for name in ("weaker_random", "weaker_label_blocks"))
    winners = [name for name, score in ranks.items()
               if name.startswith("shortcut_") and score > 0]
    ties = [name for name, score in ranks.items()
            if name.startswith("shortcut_") and score == 0]
    assert len(winners) == 5 and ties == ["shortcut_more_samples"]
    stored = json.loads((AUDIT / "stored_reference_scores_test.json").read_text())
    for experiment, values in summary["raw_metrics"]["reference_seed0"].items():
        previous = stored["experiments"][experiment]["results"]["bipartite"]
        assert all(abs(value - previous[key]) < 1e-12 for key, value in values.items())

    # The original pre-audit state is retained separately from experiment caches.
    original_state = AUDIT / "_state"
    restored = {}
    for relative in json.loads((original_state / "manifest.json").read_text()):
        restored[relative] = file_hashes(ROOT / relative) == file_hashes(original_state / relative)
    assert all(restored.values()), restored
    base = (AUDIT / "start_commit.txt").read_text().strip()
    exclusions = [":!redteam", ":!REDTEAM.md", ":!action.yaml", ":!README.md",
                  ":!manifest.json", ":!trajectory", ":!jobs"]
    difference = subprocess.check_output(
        ["git", "diff", "--name-only", base, "--", ".", *exclusions],
        cwd=ROOT, text=True).splitlines()
    assert difference == [], difference
    parsed = []
    for path in sorted(AUDIT.glob("*.py")):
        ast.parse(path.read_text(), filename=str(path))
        parsed.append(str(path.relative_to(ROOT)))
    shell_paths = sorted(AUDIT.glob("*/run.sh")) + [AUDIT / "run_all.sh"]
    for path in shell_paths:
        subprocess.run(["bash", "-n", str(path)], check=True)
    evidence = {
        "job_id": "e175191e-e18", "attempts": len(records),
        "accepted": 15, "rejected": 3, "winning_shortcuts": winners,
        "tying_shortcuts": ties, "all_test_commands_have_no_arguments": True,
        "all_evaluators_unchanged": True, "reference_matches_stored": True,
        "experiment_files_restored_to_pre_audit_state": restored,
        "original_gym_diff_excluding_system_metadata_and_action": difference,
        "python_sources_parsed": parsed, "shell_scripts_checked": len(shell_paths),
    }
    (AUDIT / "final_validation.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
