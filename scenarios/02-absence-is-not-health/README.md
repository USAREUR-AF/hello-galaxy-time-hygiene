# 2 — Absence of evidence is not evidence of health

**Run:** `python3 run.py` (or `bin/hello-time 2`) · **Needs:** nothing

Six hosts, one set of rules, six different truths. Two of the six claim to be
healthy and neither is shown as green: one cannot sign what it says, the other
has not been heard from since. Both read `idle` — UNCONFIRMED.

The rule being demonstrated is the one status boards get wrong: a surface that
renders an unattested or stale host as green, or that quietly shows the last
good value, has converted *I do not know* into *fine*. That conversion is what
gets acted on.

It also separates `idle` from `unmetered`. Hosts reporting but unconfirmable is
a different fact from no host reporting at all. Collapse them and you cannot
tell a broken fleet from a broken dashboard.

Reference: [../../docs/two-watches.md](../../docs/two-watches.md), and
`lib/verdict.py` for the ~90-line rule this mirrors from production.
