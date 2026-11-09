# Hardening report

**Better results now score higher, and every major shortcut in `REDTEAM.md` except over-budget brute-force search is closed.** The held-out test now draws its own secret-seeded instances inside `eval/test/` and runs every registered ranker on inputs it supplies. It accepts only a full permutation of each instance's candidate pool and recomputes every number itself.

The reproduction now follows the paper's direction on both tasks. The near-chance `synthetic_planes` stand-in, on which the reference lost to leave-one-out (LOO), was replaced by the paper's own `fried` dataset, regenerated from its published definition.

All numbers below come from jobs `cc16bb60-089` and `553bd7c8-3f6` (both exit 0; the second regenerated the reference from the final code and passed `python validate.py --compare --post-design`). The checks used 100 held-out instances per dataset, the same instances for every method, so all comparisons are paired. Aggregates are in `redteam/hardening/summary.json` and `summary.md`, and per-check logs and scores are in `redteam/hardening/<check>/`. Per-instance held-out curves count as test feedback, so they stayed in gitignored `tmp/`.

## Scoring rule used for the "gain" columns

The gain of attempt *a* is Σ_exp weight × Σ_metric |coefficient| × direction × (a − reference) / σ. Here σ is the population standard deviation of the aggregate metric across the 15 scored attempts in the "after" table. The same expression evaluated per instance gives paired gains; their standard error (SE) is the test's noise, and z = gain / SE. The "before" column is copied from `REDTEAM.md`, which normalized over its own cohort and used the old metric set. Compare before and after by sign and order, not by magnitude.

## 1. Do better results score higher?

| Attempt | Before: digits / synthetic mean acc | Before: gain | After: digits / fried mean acc | After: gain (paired SE, z) |
|---|---|---:|---|---:|
| Reference (paper's bipartite selector) | 0.7977 / 0.5585 | 0 | 0.7943 / 0.7326 | 0 |
| Better: reset coverage once saturated (same 80 utility calls) | 0.8040 / 0.5635 | +0.044 | 0.8019 / 0.7442 | **+0.401** (0.045, z = +8.9) |
| Better: validation prototypes (≤ 55 utility calls) | 0.8068 / 0.5567 | +0.342 | 0.8065 / 0.7447 | **+0.715** (0.086, z = +8.3) |
| Better: validation-utility greedy within the 1000-retraining budget | — | — | 0.7931 / 0.7546 | **+0.699** (0.091, z = +7.7) |
| Same method, 10× sampled utilities (800) | 0.7977 / 0.5585 | 0 | 0.7943 / 0.7331 | +0.016 (0.019, z = +0.8): a tie, as it should be |
| Weaker: random order | 0.7470 / 0.5391 | −1.211 | 0.7326 / 0.7104 | **−2.193** (0.102, z = −21.5) |
| Weaker: one class block at a time | 0.4990 / 0.5252 | −3.504 | 0.4984 / 0.6016 | **−8.198** (0.073, z = −112.8) |
| Baseline: Monte Carlo Data Shapley | 0.7710 / — | — | 0.7730 / 0.7286 | −0.848 (0.092, z = −9.2) |
| Baseline: leave-one-out | 0.7203 / 0.5650 | — | 0.7219 / 0.7012 | −2.907 (0.108, z = −26.8) |

Before, the coverage-reset variant's synthetic-task gain sat inside the noise (paired t = 0.8 over 10 seeds), and the prototypes variant lost on that task. Now both better variants beat the reference on **both** tasks:
- Coverage reset: +0.0076 digits (paired t = 7.8), +0.0115 fried (t = 6.6).
- Prototypes: +0.0122 (t = 8.4) and +0.0121 (t = 4.5).

Both weaker variants lose by many standard errors.

## 2. Major shortcuts: fix and score before → after

| Shortcut (REDTEAM) | Fix | Before | After |
|---|---|---:|---|
| **Rebuilt answers**: the visible `load_task` regenerated the test labels; greedy on test accuracy | `eval/test/` generates held-out instances from a secret seed with its own copy of the generators. Methods get only pool + validation, and the instance `seed` is a method seed unrelated to the split. | +1.717 | Matched 0 of 200 held-out instances to any visible seed (0-2000 or the given seed). Falls back to the reference, so its gain is 0.000: no information gained. |
| **Larger pool**: the evaluator used the submitted `train_size` | Pool size is fixed by the instance; the ranking must be a permutation of exactly that pool. | +0.944 | **Fails the run**: "ranks 600 points; the candidate pool has 100". |
| **Seed cherry-pick / duplicated evidence** | The evaluator enumerates its own 200 instances and needs one ranking for each; it no longer accepts any set of files. | +0.744 | Skipping half the instances **fails the run**. Copying one ranking to every instance is scored per instance: −2.301 (at random level). |
| **Replaced task**: the edited visible `data/tasks.py` defined the test | `eval/test/` does not import `data/`. | +5.222 | `data/tasks.py` replaced by one-hot labels: the reference's held-out scores are unchanged to the last digit; the shortcut's class-interleaved order scores −1.192. |
| **Forged fields / forged `scores_test.json`** | Only `ranking` is read. The scores file is deleted at start and on any failure, and written only at the end. | −1.211 (already failed) | The forged perfect `scores_test.json` was overwritten with the true score, −2.193 (random level). |
| Empty / duplicate / NaN / float indices; singleton pool | Strict validation: full permutation, JSON integers. Any failure exits non-zero and leaves no scores file. | Rejected; singleton accepted at −5.421 | All **fail the run**, including the singleton ("ranks 1 points; the candidate pool has 100"). |
| Tenfold sampling (honest higher compute) | None needed | 0 | +0.016 (z = 0.8): a tie. |
| **Brute-force selection**: every remaining candidate at every step | **Not closed by the test**; see §3. | +0.734 | +0.913 (z = +9.4) |

The hidden test runs with no arguments (`bash scripts/evaluate_test.sh`) and scores every ranker in `scripts/rankers/*.sh`. Its scores for the four registered methods were identical, to the last digit, to an independent rerun inside the cohort check.

## 3. Shortcuts left open, and why

1. **Brute-force validation greedy (pays: +0.913).** It uses 5,050 retrainings per digits instance and 1,275 per fried instance. The paper limits every method to 1,000 retraining steps. The evaluator runs rankers but cannot count retrainings: a ranker can always train the learner itself on the validation set it is given. So the cap is a written rule (`scoring/CONSTRAINTS.md`, `DIRECTION.md`) for the grader. Scaling the pools up until O(n²) search becomes infeasible would have abandoned the paper's 100/50-point protocol and diluted the selection-curve metric, so I did not.

   Most of what brute force earns is honest headroom. The same greedy kept within the budget (≤ 10 or 20 sampled candidates per step, ≤ 1000 retrainings) scores +0.699 and reaches 0.7546 on fried, against brute force's 0.7558. On digits, brute force does not beat the reference on mean accuracy (+0.0015, t = 0.9). Its digits gain comes from a smaller largest accuracy drop between consecutive prefixes (0.016 vs 0.024), a real stability improvement.

2. **External copies of the data.** The held-out instances come from public sources: scikit-learn digits, and Friedman #1. A ranker could load the full digits set, or generate more fried data, and use it as a large proxy test set. That would likely pay a lot (the old rebuilt-answers shortcut, which used exact test labels, gained +1.7). Closing it would need an obfuscation such as a secret per-instance rotation of the features, applied to the visible instances as well. That changes the problem for every method, so it is not a small fix. It is forbidden in `CONSTRAINTS.md` and left to the grader. I did not run it.

3. **Reading `eval/test/` at test time.** Rankers run in the same filesystem as the evaluator, so a ranker could read the secret seed from the evaluator's source. This is forbidden and obvious in review; no defense was built (per the brief, no defenses against the environment).

## 4. Reference before → after

| | Before (10 held-out seeds) | After (100 held-out instances) |
|---|---|---|
| digits mean accuracy | 0.7977 | 0.7943 (early10 0.443, early20 0.595, tail 0.844, max drop 0.024) |
| second task mean accuracy | synthetic_planes 0.5585 (lost to LOO 0.5650) | fried 0.7326 (early10 0.656, early20 0.689, tail 0.761, max drop 0.062) |

The paper's direction on the held-out test:
- **Digits:** reference 0.7943 > Data Shapley 0.7730 (paired t = 11.7) > random 0.7326 > LOO 0.7219. The paper reports 0.764 > 0.680 (LOO) / 0.649 / 0.619.
- **Fried:** reference 0.7326 > Data Shapley 0.7286 > random 0.7104 > LOO 0.7012. The paper reports 0.741 > 0.710 / 0.702 / 0.698.

The fried mean-accuracy margin over Data Shapley is small and within noise (+0.004, paired t = 1.4). The paper's margin was +0.031. The reference is clearly ahead early (early10 0.656 vs 0.598; early20 0.689 vs 0.657), so the composite separates them (z = 9.2).

The reference's pooled curve spread on fried (0.068) matches the paper's ±0.065.

## 5. Headroom check

The reference sits at the bound of **no** scored metric (bounds are 1 for the accuracies and 0 for the drop): mean 0.794 / 0.733, early10 0.443 / 0.656, early20 0.595 / 0.689, tail 0.844 / 0.761, max drop 0.024 / 0.062. Three variants that use no more information than the reference, and stay within the budget, beat it by 7.7-8.9 paired standard errors. No single simple variant reaches a bound.

So no headroom experiment was added. Exact dynamic programming over subsets, the brute force the paper's method exists to avoid, is infeasible at pools of 100 and 50. The polynomial greedy is discussed in §3.

The baselines still make sense: random is 0.062 / 0.022 below the reference, with room above.

## 6. Other changes and why

- **Scored metrics now limited to what the paper measures:** curve mean (coefficient 1.0), early10 (0.5), early20 (0.6), tail (0.4, the constraint that early gains are not bought at larger budgets), and max one-step drop (0.2, the paper's "fewer fluctuations"). Weights stay digits 0.6, fried 0.4. The coefficients are the previous ones for the metrics kept, now written as magnitudes with `higher_is_better`.
- **Removed metrics:**
  - `worst_prefix_accuracy`: essentially the class prior of the first pick, with 0.002 of headroom.
  - `early_label_balance`: not a paper quantity.
  - `final_accuracy` and `selection_budget`: identical for every valid ranking.
  - Across-seed `mean_accuracy_std`: rewarded seed cherry-picking.
- **Paper ±:** `curve_accuracy_std` (pooled spread over prefixes and instances, unscored) is reported to match the paper's Table 1 ± column, which `reference.json` now keeps under that name. It previously sat in the wrong metric.
- **Test size:** 10 → 100 instances per dataset, so the gains in §1 are 7-9 paired standard errors. Splits are fixed by secret seeds; the reference is deterministic, and 10× more subset sampling leaves its held-out mean accuracy unchanged on 189 of 200 instances.
- **Visible slice:**
  - Uses the same ranker interface (seeds 1-20).
  - Visible instances now give methods a seed decoupled from the split seed. Previously the random baseline's permutation came from the same random-number stream that built the pool, which inflated it by 0.015 (3.9 SE). After the fix, train and test agree for every method within about 0.004 mean accuracy.
- **CPU threads:** `OMP/OPENBLAS/MKL_NUM_THREADS` default to 1 in all entry scripts. One-CPU jobs were otherwise oversubscribed about 25×. The hidden test takes about 9 minutes for the four registered rankers.
- **Code changes:** the method and baseline algorithms are unchanged; only their input/output now goes through instance files. `eval/evaluate_rankings.py` was removed. Per-instance held-out curves are never written to the repository.

## 7. Not fixed / caveats, stated plainly

- Over-budget brute force (§3.1) and use of external copies of the public data (§3.2) still pay if a grader misses them.
- The paper's stability claim does not reproduce here. The reference has the *largest* max one-step drop on fried (0.062 vs 0.039-0.052 for the baselines) and is mid-pack on digits. That metric stays scored as room for improvement.
- Absolute accuracies differ from the paper (e.g. random on digits 0.733 vs 0.619) because of class-balanced pools and standardized features; the ordering of methods matches. Fried is regenerated from its definition, not the identical OpenML rows.
- The older audit scripts in `redteam/` (`generate.py`, `harness.py`, `*/run.sh`) target the previous interface and no longer run; the current checks are in `redteam/hardening/`. To rerun them: `python -m redteam.hardening.harness --force && python -m redteam.hardening.summarize` (about 1.5 h on one CPU).
