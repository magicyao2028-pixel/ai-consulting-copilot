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

## Failure and recovery

If lineage construction fails, inspect the named claim node and evidence ID. Correct the source register or claim citation; do not delete freshness, reliability or contradiction gates to force a recommendation.

## Real-pilot boundary

A real pilot requires accountable evidence owners, access control, retention, source verification, conflict resolution, approved thresholds and a human go/no-go owner. This graph demonstrates declared lineage, not source truth, forecast accuracy or consulting validity.
