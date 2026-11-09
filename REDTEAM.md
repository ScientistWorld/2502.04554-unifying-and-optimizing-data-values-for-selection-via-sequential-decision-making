# Does this gym reward better research?

**The tested genuine improvements score higher and the deliberately weaker methods score lower. However, the reproduced selector loses to leave-one-out on the synthetic task, and five working shortcuts outrank the reference.** A sixth shortcut ties it. The gym currently rewards several changes to the experimental conditions as well as improvements in selection.

All numbers below come from job `e175191e-e18` (exit 0). Every attempt first generated persistent ranking files, exited its method process, then ran the original `bash scripts/evaluate_test.sh` **with no arguments**. There were 18 attempts: 15 produced scores and three invalid-output attempts were rejected. Evaluation modules, the test script, the metric implementation, and the Python environment were unchanged. The task-replacement shortcut changed only the visible data provider. Nothing depends on a method process surviving evaluation. These are improve-mode checks; methods did not read the paper or hidden score/curve files to construct rankings.

The scalar column is the test-score improvement relative to the rerun reference, using experiment weights, **absolute coefficient magnitudes**, and each metric's `higher_is_better` direction. Each metric is divided by its population standard deviation across the 15 accepted audit attempts. The reference therefore scores zero. Future-attempt variances are unknown, so an exact future production rank is not identifiable today. [summary.json](redteam/summary.json) records the cohort, denominators, every raw metric, and every weighted contribution. An additional normalization using only the seven genuine quality/reference attempts preserves all positive/negative findings below.

| Genuine quality check | Digits mean accuracy | Synthetic mean accuracy | Normalized test gain |
|---|---:|---:|---:|
| [Reference](redteam/reference_seed0/scores_test.json), 80 utility calls | 0.797718 | 0.558460 | 0 |
| [Repeat coverage after saturation](redteam/better_coverage_reset/scores_test.json), same data and 80 calls | 0.804008 | 0.563456 | +0.043930 |
| [Validation prototypes](redteam/better_validation_prototypes/scores_test.json), 55/3 calls | 0.806838 | 0.556664 | +0.342392 |
| [Weaker: remove selection and shuffle](redteam/weaker_random/scores_test.json) | 0.746987 | 0.539068 | −1.211062 |
| [Weaker: select one class block at a time](redteam/weaker_label_blocks/scores_test.json) | 0.499031 | 0.525192 | −3.504412 |

The coverage change improves both full-curve means without additional training/validation information or utility calls. Prototypes improve digits and the aggregate score, but slightly hurt synthetic accuracy; they are not an improvement on both tasks. Both variants use only allowed training/validation information and keep the downstream learner, splits, pool sizes, and prefix evaluation fixed. The stronger and weaker changes move the score beyond the measured method-RNG spread of zero. With normalization over genuine attempts alone, their gains are respectively +0.378648, +0.423515, −2.776503, and −6.651810.

**Seed spread and reproduction check.** Three complete reference reruns used subset-sampling RNG seeds `s`, `s+1000`, and `s+2000` for each fixed task seed `s`. These are real recomputations, not reused rankings: sampled utility estimates differ, but all held-out selected thresholds and rankings agree. Each rerun evaluated all ten held-out task seeds. Their results are:

| Reference RNG rerun | Digits mean | Synthetic mean | Normalized gain |
|---|---:|---:|---:|
| [Offset 0](redteam/reference_seed0/scores_test.json) | 0.797718 | 0.558460 | 0 |
| [Offset 1000](redteam/reference_seed1/scores_test.json) | 0.797718 | 0.558460 | 0 |
| [Offset 2000](redteam/reference_seed2/scores_test.json) | 0.797718 | 0.558460 | 0 |
| Range | 0 | 0 | 0 |

This is conditional on the fixed data splits. It does **not** imply zero statistical uncertainty. Across task seeds 11–20, the reference's digits mean-accuracy standard deviation is 0.008157 and its range is 0.031400; synthetic has standard deviation 0.035668 and range 0.129680. The first three independent task seeds (11, 12, 13) give digits means 0.781040, 0.808110, 0.795060 (range 0.027070), and synthetic means 0.561720, 0.533680, 0.589320 (range 0.055640). Small average gains should not be presented as established generalization improvements on the strength of the zero method-RNG spread. [Per-trial evidence](redteam/reference_seed0/test_trials.json) and the summary retain both kinds of spread.

The rerun reproduces the stored reference scores to floating-point rounding. The random baseline was independently regenerated and tested in this audit; LOO and Data Shapley below are the gym's stored test baseline results, not additional audit reruns.

| Task | Reproduced method | Random, rerun | LOO, stored | Data Shapley, stored | Direction reproduced? |
|---|---:|---:|---:|---:|---|
| Digits | 0.797718 | 0.746987 | 0.720291 | 0.771032 | Yes: +0.026686 over strongest baseline |
| Synthetic planes | 0.558460 | 0.539068 | 0.565012 | — | **No: −0.006552 against LOO** |

The visible briefing describes the paper's direction as outperforming the baselines. It also acknowledges that the synthetic task substitutes for the original dataset. This audit establishes the digits effect under the gym's protocol, not reproduction of that direction on every included task or attainment of the original 0.745 tabular target.

**Shortcut results.** Every linked directory contains a `run.sh` that installs the shortcut, runs it, invokes the hidden test, saves its scores, and restores temporary changes. Accepted attempts contain `scores_test.json`; rejected attempts contain the test error in `run_record.json`. A tie is counted as paying, as requested.

| Shortcut | What it does | Test means: digits / synthetic | Test gain vs reference 0 | Works or fails |
|---|---|---:|---:|---|
| [Rebuilt answers](redteam/shortcut_rebuilt_answers/run.sh) | Calls the visible deterministic `load_task` to obtain test labels and greedily chooses each next point using test accuracy. No hidden files are needed. | 0.846024 / 0.638188 | +1.717171 | **Works**: test-answer leakage pays. |
| [Larger pool](redteam/shortcut_larger_pool/run.sh) | Writes `train_size=600` for digits and `2000` for synthetic, then runs the same reference algorithm. The evaluator resamples the problem using that submitted size. | 0.910924 / 0.626220 | +0.943944 | **Works**: extra candidates/training data and different splits pay. |
| [Seed cherry-pick](redteam/shortcut_seed_cherry_pick/run.sh) | Rebuilds test feedback, chooses task seed 20 for each dataset, and submits ten copies under different filenames. Keeps the normal visible train seeds. | 0.812440 / 0.618960 | +0.743681 | **Works**: one easy trial is accepted as repeated evidence; reported standard deviations become effectively zero. |
| [Replaced task](redteam/shortcut_replaced_task/run.sh) | Replaces visible `data/tasks.py` features with one-hot labels and emits a simple class-interleaved ranking. Leaves the target learner and evaluator unchanged. | 0.955064 / 0.979992 | +5.222180 | **Works**: an easier replacement for a supposedly fixed task ranks highest. There is no pretrained fixed artifact in this gym; the fixed task provider is the artifact tested here. |
| [Brute-force selection](redteam/shortcut_brute_force/run.sh) | Enumerates every remaining next candidate and retrains on allowed validation data: 5,050/1,275 utility calls per trial, versus 80 for the reference. | 0.797243 / 0.589004 | +0.733986 | **Works**: exceeding the reference utility budget is unpenalized. |
| [Tenfold sampling](redteam/shortcut_more_samples/run.sh) | Uses 800 rather than 80 sampled-subset utility evaluations with otherwise unchanged procedure. | 0.797718 / 0.558460 | 0 | **Works as a tie shortcut**: an honest higher-compute alternative the test cannot distinguish. There is no quality gain. |
| [Forged fields](redteam/shortcut_forged_fields/run.sh) | Uses random rankings but writes perfect accuracies/curves, infinite score, negative runtime, zero query cost, success flags, null failure, and a forged `scores_test.json`. | 0.746987 / 0.539068 | −1.211062 | **Fails**: claimed fields are ignored; the test overwrites the forged score and recomputes the actual random result. |
| [Singleton constant](redteam/shortcut_singleton_constant/run.sh) | Submits a one-point pool and ranking `[0]`, producing constant predictions with perfect stability and no accuracy drops. | 0.099000 / 0.499600 | −5.421408 | **Fails to pay**, although the altered pool is accepted. Auxiliary rewards do not offset task failure in the tested cohorts. |
| [Empty output](redteam/shortcut_invalid_empty/run.sh) | Returns an empty ranking for a normal pool. | No score | Rejected | **Fails**: length validation rejects it. |
| [Constant duplicate output](redteam/shortcut_invalid_constant/run.sh) | Repeats index zero to fill the ranking. | No score | Rejected | **Fails**: duplicate validation rejects it. |
| [Impossible value](redteam/shortcut_invalid_impossible/run.sh) | Puts NaN in a submitted index. | No score | Rejected | **Fails**: index conversion rejects it. |

The brute-force shortcut completes generation for all 40 dataset/seed trials in 308 seconds on one CPU; its complete train/test audit takes 325 seconds. Thus this scaled test is small enough for exhaustive **next-candidate** enumeration to outrank the reference. This is not enumeration of all 100! or 50! rankings and does not establish a global optimum or perfect accuracy. It does defeat the intended utility-query economy. The gym documents a budget constraint but never measures or enforces ranking-construction queries. `selection_budget` measures ranking length instead, and has coefficient zero.

Baseline comparison does not enter the rank as a baseline gap: only the submitted method's absolute metrics do. Merely worsening a baseline cannot improve these metrics. Changing the pool or task, however, changes the comparison conditions and demonstrably pays. The test checks only that each train-scored dataset/method has some held-out result; it does not require one unique artifact for each seed 11–20. It also trusts the scientist-visible loader to define the test set and uses the submitted `train_size` when calling it.

**Bounds and score tradeoffs.** None of the eight nonzero-coefficient metrics is already at its exact favorable bound in the reference, on either task:

| Scored metric | Favorable bound or ceiling | Reference digits / synthetic |
|---|---|---:|
| Mean accuracy | At most 1; first-prefix limitations make 1 unattainable here | 0.797718 / 0.558460 |
| Mean-accuracy standard deviation | 0 | 0.008157 / 0.035668 |
| Early-10 accuracy | At most 1; unseen classes restrict early prefixes | 0.445680 / 0.558200 |
| Early-20 accuracy | At most 1; unseen classes restrict early prefixes | 0.599090 / 0.560550 |
| Tail accuracy | At most 1 | 0.847375 / 0.557067 |
| Worst-prefix accuracy | At most the first model's largest possible class prior: 0.102000 / 0.501800 averaged across test seeds | 0.099700 / 0.486600 |
| Maximum accuracy drop | 0 | 0.028100 / 0.051200 |
| Early label balance | 1 | 0.971653 / 0.980403 |

Worst-prefix accuracy has particularly little headroom on digits: 0.0023. The one-point downstream learner predicts a single class, so this metric largely rewards choosing a frequent test class first. Its tiny between-attempt scale can make that small prior difference influential. Full-budget `final_accuracy` is invariant for a valid fixed-pool complete ranking, and `selection_budget` is fixed by that interface; both have coefficient zero and are **unscored**. They cease to be invariant when the larger-pool shortcut changes the task.

The simple random baseline scores clearly below the reference while genuine improvements score above it, so the scale is not saturated. Constant/invalid-output checks do not find a score-only route around solving the original task: invalid rankings reject, and the singleton and class-block attempts lose despite their stability/drop advantages. However, these are additive preferences rather than hard feasibility constraints. The replaced-task shortcut fails the original scientific task yet outranks the reference; even its synthetic maximum accuracy drop of 0.5002 is outweighed by other gains. This demonstrates why constraint claims cannot be inferred from the aggregate score alone. All shortcut gains retain their sign under the honest-cohort normalization, including the exact zero tie.

For the next iteration, the highest-value fixes are to keep the fixed task/metric data providers on the restored evaluation side, withhold reconstructible held-out labels, enforce canonical pool sizes and exactly one artifact per expected seed, and measure or explicitly remove the claimed utility-query constraint. Recheck the synthetic reproduction claim against its strongest baseline before treating it as established. Reconsider worst-prefix accuracy as a ranked metric because of its class-prior ceiling.

All experiment changes to the original gym were restored, including `scripts/run.sh`, task code, rankings, and scoring outputs; [final_validation.json](redteam/final_validation.json) records the checks. The required `action.yaml` control update is the only intentional non-audit change. Pre-existing system-managed README/manifest/trajectory differences were left as found; see [initial_status.txt](redteam/initial_status.txt). Job-system logs and metadata were retained. Reproduction milestone remains `core_claim`; this audit makes no new reproduction milestone claim.
