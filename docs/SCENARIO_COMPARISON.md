# Scenario Comparison

## Purpose

v0.4 separates evidence from decision policy. A reviewer can declare multiple threshold scenarios, run each against the same governed evidence register and see whether the pilot decision changes. This is sensitivity analysis, not a forecast.

## Input contract

Each scenario has a unique `scenario_id`, a label and three non-negative thresholds: monthly support volume, repetitive-contact share and first-response hours. Share must remain between 0 and 100. At least two scenarios are required.

## Safety and evidence controls

- Thresholds change policy, never source eligibility or evidence values.
- Stale, future-dated and unverified sources remain excluded in every scenario.
- A material current-evidence conflict or missing required metric blocks every scenario; thresholds cannot bypass an evidence gate.
- Normalized interview candidates remain outside the evidence register. Only attributable approved observations can enter the normal evidence path.
- Every scenario records the evidence IDs used and still requires a human go/no-go decision.

## Reproduce the synthetic case

```bash
PYTHONPATH=src python -m consulting_copilot.scenario_cli \
  data/sample_engagement.json data/sample_scenarios.json \
  --output examples/scenario_comparison.json
```

The baseline and cautious policies support a bounded pilot; the strict policy does not. That transition demonstrates policy sensitivity using synthetic values. It does not establish an optimal threshold or a real business outcome.
