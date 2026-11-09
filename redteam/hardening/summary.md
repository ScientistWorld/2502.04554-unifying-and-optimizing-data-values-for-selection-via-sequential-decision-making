| Attempt | digits mean acc | fried mean acc | composite gain | paired SE | z |
|---|---:|---:|---:|---:|---:|
| brute_force_greedy | 0.7958 | 0.7558 | +0.913 | 0.097 | +9.4 |
| validation_prototypes | 0.8065 | 0.7447 | +0.715 | 0.086 | +8.3 |
| budgeted_greedy:budgeted_greedy | 0.7931 | 0.7546 | +0.699 | 0.091 | +7.7 |
| coverage_reset | 0.8019 | 0.7442 | +0.401 | 0.045 | +8.9 |
| more_samples_800 | 0.7943 | 0.7331 | +0.016 | 0.019 | +0.8 |
| bipartite | 0.7943 | 0.7326 | +0.000 |  |  |
| rebuilt_answers:rebuilt_answers | 0.7943 | 0.7326 | +0.000 |  |  |
| replaced_task:bipartite | 0.7943 | 0.7326 | +0.000 |  |  |
| datashap | 0.7730 | 0.7286 | -0.848 | 0.092 | -9.2 |
| replaced_task:round_robin | 0.7697 | 0.7152 | -1.192 | 0.074 | -16.2 |
| random | 0.7326 | 0.7104 | -2.193 | 0.102 | -21.5 |
| forged_fields:forged_fields | 0.7326 | 0.7104 | -2.193 | 0.102 | -21.5 |
| copied_ranking:copied_ranking | 0.7346 | 0.7067 | -2.301 | 0.097 | -23.7 |
| loo | 0.7219 | 0.7012 | -2.907 | 0.108 | -26.8 |
| label_blocks | 0.4984 | 0.6016 | -8.198 | 0.073 | -112.8 |

| Check | test exit | message |
|---|---:|---|
| budgeted_greedy | 0 |  |
| cohort | 0 |  |
| cohort_train | 0 |  |
| copied_ranking | 0 |  |
| forged_fields | 0 |  |
| invalid_duplicate | 1 | FAILED: digits_h000.json ranking is not a permutation of the candidate pool |
| invalid_empty | 1 | FAILED: digits_h000.json ranks 0 points; the candidate pool has 100 |
| invalid_float | 1 | FAILED: digits_h000.json ranking entries must be JSON integers |
| invalid_nan | 1 | FAILED: digits_h000.json ranking entries must be JSON integers |
| larger_pool | 1 | FAILED: digits_h000.json ranks 600 points; the candidate pool has 100 |
| rebuilt_answers | 0 |  |
| replaced_task | 0 |  |
| singleton | 1 | FAILED: digits_h000.json ranks 1 points; the candidate pool has 100 |
| skip_half | 1 | FAILED: no ranking written for held-out instance digits_h001 |
