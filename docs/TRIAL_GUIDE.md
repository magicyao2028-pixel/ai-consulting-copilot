# Reviewer Trial Guide

## Purpose

This 15–20 minute offline trial builds a cited decision memo, converts its evidence-to-claim relationships into a machine-readable lineage graph, and proves that unknown or ineligible evidence cannot support a claim.

## Clean start

```bash
python -m venv .venv
python -m pip install -e .
consulting-trial
```

Expected result: the trial passes, the memo remains `recommendation_ready`, all nine claim objects have eligible citations, and a synthetic unknown citation fails closed.

The v1.2 Trial additionally requires a valid actual `decision_metric_unit_receipt` for both ready and conflicted memos. The three declared units are contacts/month, percent and hours. Five negative probes reject minutes, contacts/day, ratio, a missing unit and a typed-container unit bypass before generating recommendations. Every receipt field/type is required by PASS, including exact IDs/counts, no conversion, no evidence mutation, human approval and zero external action. Returned triage/history/replay/reconciliation controls are also required. All fourteen indexed evidence claims must validate.

A unit failure is not auto-converted. Review the source definition and prepare values in the declared units, then rerun. Trial PASS proves these offline checks, not measurement truth, an approved pilot, source auditing or a new static-site deployment.

The ultimate Trial consumer rechecks the actual returned receipt and five uniquely identified, typed probe outcomes even if the helper retains `passed=true`. Missing/duplicate probes, changed approval/execution flags and bool/int substitutions deny PASS. The core action summary uses that same returned receipt rather than a different upstream copy.

## Failure and recovery

If lineage construction fails, inspect the named claim node and evidence ID. Correct the source register or claim citation; do not delete freshness, reliability or contradiction gates to force a recommendation.

## Real-pilot boundary

A real pilot requires accountable evidence owners, access control, retention, source verification, conflict resolution, approved thresholds and a human go/no-go owner. This graph demonstrates declared lineage, not source truth, forecast accuracy or consulting validity.
