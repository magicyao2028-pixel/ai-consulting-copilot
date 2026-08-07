# Handoff

## Current state

- Release stage: v0.1 product-validation prototype.
- Maintenance completed: 0/10.
- Core flow: validate evidence -> exclude unverified items -> enforce minimum metrics -> create cited findings/options/risks -> recommend or abstain -> render memo.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m consulting_copilot.cli data/sample_engagement.json --json-output examples/decision_memo.json --markdown-output examples/decision_memo.md
```

## Next maintenance round

M1 should detect contradictory metric claims and flag stale evidence before recommendation. It must preserve unverified-evidence exclusion, citation integrity and insufficient-evidence abstention.

## Known limitations

- synthetic reference case and illustrative thresholds;
- input reliability labels are trusted rather than audited;
- deterministic English output only;
- no interview ingestion, web research, LLM, database, authentication or real user study;
- static page and Python output are maintained separately.
