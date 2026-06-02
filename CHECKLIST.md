# Reproduction Checklist

Check off items as you complete them. Order does not matter; keep this aligned with the actual state of the repository.

## Briefing

- [x] `briefing/problem.md` is method-agnostic
- [x] `briefing/evaluation.md` is method-agnostic
- [x] `briefing/method.md` describes the paper's sequential DP and bipartite surrogate framework
- [x] `briefing/overview.md` summarizes the paper and headline claims

## Scoring Documentation

- [x] `scoring/EXPERIMENTS.md` describes high-level experiment purposes
- [x] `scoring/TARGETS.md` includes benefit metrics and constraint metrics
- [x] `scoring/CONSTRAINTS.md` states fixed resources and protocol rules for future scientists
- [x] `scoring/DIRECTION.md` scopes future improvements to ordered data selection

## Scoring Artifacts

- [x] `scoring/reference.json` records paper targets with the same experiment and metric structure as scores
- [ ] Workspace validated via `python validate.py`
- [ ] `scoring/scores.json` records reproduced numbers with the same experiment and metric structure as reference
- [ ] Every experiment in `scoring/TARGETS.md` appears in both JSON scoring files once those files exist
- [ ] Every experiment in `scoring/scores.json` is summarized in `scoring/EXPERIMENTS.md`

## Code

- [x] Evaluation code in `eval/`
- [x] Method implementation in `method/`
- [x] Baseline implementation in `baseline/` if used

## Scripts

- [x] `scripts/evaluate.sh`
- [x] `scripts/reproduce.sh`
- [x] `scripts/download.sh` is idempotent and self-contained
- [x] `scripts/baseline.sh` if applicable
- [x] `scripts/run.sh` runs the submitted reproduction job

## Environment

- [x] `environment/container.def`
- [x] `environment/setup.sh` uses setup-time installs only

## Data

- [ ] Dataset acquisition is documented and reproducible
- [ ] Downloaded or generated large files are ignored or placed under the allowed downloads location
- [ ] Training and evaluation preprocessing are consistent

## Milestones

- [x] `method_runs` - executes end-to-end without errors
- [ ] `core_claim` - minimum experiment supports central claim
- [ ] `core_claim_plus` - additional settings
- [ ] `secondary_claims`
- [ ] `majority`
- [ ] `near_complete`
- [ ] `full`
