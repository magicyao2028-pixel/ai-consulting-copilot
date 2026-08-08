# Handoff

## Current state

- Release stage: v0.2 product-validation prototype.
- Maintenance completed: 1/10.
- Core flow: validate evidence -> assess reliability and age -> detect current metric conflicts -> enforce minimum metrics -> create cited findings/options/risks -> recommend or abstain -> render memo.
- Public data: synthetic only.
- Runtime cost: zero paid API dependency.

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m consulting_copilot.cli data/sample_engagement.json --json-output examples/decision_memo.json --markdown-output examples/decision_memo.md
```

## Next maintenance round

M2 should normalize synthetic interview notes into candidate claims that require human approval before entering the evidence register. It must preserve all v0.2 quality gates.

## Known limitations

- synthetic reference case and illustrative thresholds;
- input reliability labels are trusted rather than audited;
- fixed source-specific freshness windows and 10% numeric conflict tolerance;
- deterministic English output only;
- no interview ingestion, web research, LLM, database, authentication or real user study;
- static page and Python output are maintained separately.
