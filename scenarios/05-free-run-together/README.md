# 5 — Free-running together beats free-running apart

**Run:** `python3 run.py` (or `bin/hello-time 5`) · **Needs:** nothing

> **Model, not product** for the mutual-sync arm. The contrast arm — per-node
> holdover — is today's posture, which is what makes the comparison worth
> running.

Eight nodes, two hours, anchor cut at the 30-minute mark. Two arms, same
crystals, same seed. Measures both watches separately as time passes:

- **spread** (internal coherence) stays flat under mutual sync and grows without
  bound under holdover
- **error against UTC** grows in both — and under mutual sync that is the
  *correct* reading to show: coherent, UTC confidence decaying, not "unhealthy"

The specific failure it isolates: holdover preserves *one node's* time, not
*mutual* time. Each isolated node extrapolates its own crystal in its own
direction, so the fabric fragments into independently drifting clocks at exactly
the moment the anchor is gone.

The model corrects offset without disciplining frequency, so the flat line sits
at a few milliseconds rather than converging to nothing. Take the *shape* — flat
versus growing — and no synchronisation-error number.
