# Handoff

## Current state

- Release stage: v0.5 trial-readiness prototype.
- Maintenance completed: 4/10.
- M3 flow: validate named threshold scenarios -> reuse one governed evidence register -> compare policy outcomes -> surface recommendation sensitivity without weakening evidence gates.
- M2 flow: validate synthetic consented notes -> normalize candidate claims -> keep evidence register empty -> record attributable human decisions -> promote approved observations as indicative evidence -> run existing evidence gates.
- Decision flow: validate evidence -> assess reliability and age -> detect current metric conflicts -> enforce minimum metrics -> create cited findings/options/risks -> recommend or abstain -> render memo.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.
- M4 evidence: deterministic evidence lineage, unknown/ineligible citation blocking, seven evidence claims, external screening and a synthetic citation-integrity regression.

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m consulting_copilot.cli data/sample_engagement.json --json-output examples/decision_memo.json --markdown-output examples/decision_memo.md
PYTHONPATH=src python -m consulting_copilot.interview_cli normalize data/sample_interview_notes.json --output examples/interview_candidates.json
PYTHONPATH=src python -m consulting_copilot.interview_cli review examples/interview_candidates.json data/sample_claim_review.json --output examples/interview_review.json
PYTHONPATH=src python -m consulting_copilot.scenario_cli data/sample_engagement.json data/sample_scenarios.json --output examples/scenario_comparison.json
PYTHONPATH=src python -m consulting_copilot.lineage_cli
PYTHONPATH=src python -m consulting_copilot.trial_cli
```

## Next maintenance round

M5 should add an accountable adjudication receipt for evidence conflicts while preserving the deterministic baseline and existing provenance gates.

## Known limitations

- synthetic reference case and illustrative thresholds;
- input reliability labels are trusted rather than audited;
- fixed source-specific freshness windows and 10% numeric conflict tolerance;
- scenario thresholds are user-declared prototype policy, not optimized or validated business standards;
- scenario thresholds must be finite; `NaN` and infinity are rejected before comparison;
- deterministic English output only;
- structured note intake only; no recording, transcription, web research, LLM, database, authentication or real user study;
- static page and Python output are maintained separately.
