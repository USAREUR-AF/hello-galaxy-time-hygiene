# The anchor ladder

External time sources did not go away when they stopped being the foundation.
They became *anchors*: opinions with weight, not authorities.

## The ladder, worst to best

| rung | what it is | typical uncertainty | notes |
|---|---|---|---|
| `self_clocking` | no external lock at all; the node's own crystal, extrapolated | grows monotonically since the last lock | an ordinary commercial oscillator is ±25 ppm — about two seconds a day, in its own direction |
| `peer_attested` | self-clocking, but corroborated by peers whose own time is better anchored | the pessimistic envelope of the corroborators, plus path delay | this is the rung internal synchronisation lives on |
| `chrony_steered` | chrony reports synchronised, but the upstream is opaque or unauthenticated | milliseconds | fine for housekeeping; not something to lean on |
| `nts_verified` | at least one authenticated network time source contributing | milliseconds | authentication matters: unauthenticated network time is trivially manipulated in transit |
| `gnss_locked` | a satellite receiver with a current fix | sub-microsecond with a pulse-per-second input | the best rung and the most attackable — jamming denies it, spoofing corrupts it |

The top rung being the most attackable is not a paradox to resolve; it is the
reason anchors are weighted opinions and not authorities. Losing the best rung
must degrade the reading, never break the fabric.

## How chrony's numbers map onto the rungs

The per-host agent reads chrony's tracking state and turns it into a verdict.
Two of its rules are worth knowing by heart, because they are the ones that
catch real faults:

- **Stratum 16 means unsynchronised.** chrony has no usable source. Verdict:
  `unknown` — not `degraded`. The node is not slightly wrong; it does not know.
- **Stratum 10 or above means orphan mode**, where the host is quoting *itself*
  as its own reference. Verdict: `degraded`, never `healthy`. This is the sneaky
  one: an orphan-mode host is perfectly self-consistent and completely
  unanchored, so every internal check it runs on itself passes.

Below that, classification is offset-and-stratum: within 1 ms at stratum 4 or
better is `healthy`; within 10 ms at stratum 6 or better is `warning`; within
100 ms is `degraded`; worse is `unknown`. `lib/verdict.py` in this repo mirrors
the production rule, and `bin/hello-time test` checks the mirror.

## Anti-spoofing, honestly

A spoofed satellite anchor must not be able to capture the ensemble. The design
answer is multi-anchor cross-check plus attestation weighting — and it is listed
as an **open item** in ADR 1037, not as a solved problem. This repo does not
demonstrate it, because there is nothing built to demonstrate.

## The per-message dimension, which is designed and not built

Separately from per-host health, there is a design (ADR 0514,
`docs/design/time-quality-attestation.md`) for a `time_quality` envelope carried
*inline on every published message*: which rung of the ladder produced this
timestamp, the 1σ uncertainty, how long since the last external lock. It exists
so a consumer can weight or filter inputs — "only fuse tracks whose timestamps
came from `nts_verified` or better" — instead of silently treating a
self-clocking edge node identically to a satellite-locked one.

It is designed and not built. No message on any goatnet carries that field today.
