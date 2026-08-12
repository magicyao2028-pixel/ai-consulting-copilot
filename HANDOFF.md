# Handoff

## Current state

- Release stage: v0.3 product-validation prototype.
- Maintenance completed: 2/10.
- M2 flow: validate synthetic consented notes -> normalize candidate claims -> keep evidence register empty -> record attributable human decisions -> promote approved observations as indicative evidence -> run existing evidence gates.
- Decision flow: validate evidence -> assess reliability and age -> detect current metric conflicts -> enforce minimum metrics -> create cited findings/options/risks -> recommend or abstain -> render memo.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m consulting_copilot.cli data/sample_engagement.json --json-output examples/decision_memo.json --markdown-output examples/decision_memo.md
PYTHONPATH=src python -m consulting_copilot.interview_cli normalize data/sample_interview_notes.json --output examples/interview_candidates.json
PYTHONPATH=src python -m consulting_copilot.interview_cli review examples/interview_candidates.json data/sample_claim_review.json --output examples/interview_review.json
```

## Next maintenance round

M3 should add configurable decision thresholds and scenario comparison. It must preserve interview approval provenance and all v0.3 evidence gates.

## Known limitations

- synthetic reference case and illustrative thresholds;
- input reliability labels are trusted rather than audited;
- fixed source-specific freshness windows and 10% numeric conflict tolerance;
- deterministic English output only;
- structured note intake only; no recording, transcription, web research, LLM, database, authentication or real user study;
- static page and Python output are maintained separately.
