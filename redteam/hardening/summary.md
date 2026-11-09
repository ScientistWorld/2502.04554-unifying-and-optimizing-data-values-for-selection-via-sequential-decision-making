| Attempt | digits mean acc | fried mean acc | composite gain | paired SE | z |
|---|---:|---:|---:|---:|---:|
| brute_force_greedy | 0.7958 | 0.7558 | +0.908 | 0.097 | +9.4 |
| validation_prototypes | 0.8065 | 0.7447 | +0.704 | 0.086 | +8.2 |
| coverage_reset | 0.8019 | 0.7442 | +0.397 | 0.045 | +8.8 |
| more_samples_800 | 0.7943 | 0.7331 | +0.015 | 0.019 | +0.8 |
| bipartite | 0.7943 | 0.7326 | +0.000 |  |  |
| rebuilt_answers:rebuilt_answers | 0.7943 | 0.7326 | +0.000 |  |  |
| replaced_task:bipartite | 0.7943 | 0.7326 | +0.000 |  |  |
| datashap | 0.7730 | 0.7286 | -0.838 | 0.091 | -9.2 |
| replaced_task:round_robin | 0.7697 | 0.7152 | -1.179 | 0.073 | -16.1 |
| random | 0.7326 | 0.7104 | -2.160 | 0.101 | -21.3 |
| forged_fields:forged_fields | 0.7326 | 0.7104 | -2.160 | 0.101 | -21.3 |
| copied_ranking:copied_ranking | 0.7346 | 0.7067 | -2.268 | 0.096 | -23.6 |
| loo | 0.7219 | 0.7012 | -2.868 | 0.108 | -26.7 |
| label_blocks | 0.4984 | 0.6016 | -8.074 | 0.072 | -111.8 |

| Check | test exit | message |
|---|---:|---|
| cohort | 0 |  |
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
