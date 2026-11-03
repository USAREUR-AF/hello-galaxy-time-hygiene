# Agreeing beats being right

*The whole mental model, in two minutes. Read this one first.*

## The instinct, and why it fails here

The obvious way to keep a fleet's clocks correct is to pick one trusted clock —
a satellite receiver, an official time server — and have everyone copy it. It is
how almost every system does it, and it works fine in a machine room.

This fabric lives where that breaks. Satellite navigation is jammed and spoofed;
the link to the outside world is cut. A design that leans on an outside clock is
a fair-weather design: it fails in exactly the weather it was built for. And
"outside clock is gone" is not the emergency case here — it is the ordinary
operating condition.

## What the fabric actually needs

Every participant stamps its own data, and consumers use those stamps to order
events, correlate a detection with an alert, age out stale tracks, and decide
which of two conflicting writes wins.

Every one of those operations needs participants to **agree with each other**.
Not one of them needs each participant to be **individually correct against
UTC**.

That distinction is the whole design:

> Two nodes that are both four seconds off, in the same direction, order their
> events perfectly. Two nodes that are each within a millisecond of UTC but
> disagree by two seconds cannot.

## So the foundation is peer agreement, not an outside reference

Instead of copying a master, every participant keeps time by continuously
listening to its peers and steering toward them — a band staying together by ear
after the conductor walks off stage. No time master, no elected authority,
nothing whose loss or capture takes the fabric's time with it. That is the same
brokerless commitment the rest of the fabric is built on, applied to time.

External references do not disappear. They are demoted from *foundation* to
**anchor**: when one is reachable, the nodes that can see it pull the whole
ensemble toward true UTC. When none is reachable, the ensemble free-runs
**together** — still ordered relative to itself, honestly less certain about UTC.

Scenario 5 makes the difference concrete against the alternative, which is what
runs today: per-node holdover, where each isolated node extrapolates its own
crystal. Holdover preserves *one node's* time. It does not preserve *mutual*
time, and it comes apart precisely when the anchor is lost.

## Which means health has two readings, not one

If UTC correctness is not what fabric ordering depends on, then a single
"is the clock right?" verdict is answering the wrong question. There are two
independent things worth knowing, and they govern different decisions:

| | governs | holds when the anchor is gone? |
|---|---|---|
| **Internal coherence** | ordering, fusion, correlation, last-write-wins | yes — that is the point |
| **UTC confidence** | certificate and token validity, cross-cluster and human-facing timestamps | no — it decays, and should say so |

A node that is internally coherent but does not know UTC is the **normal,
correct** denied-edge state. It is a fully valid publisher of tactical data and
degraded only for the operations that genuinely need UTC. Reporting it as
"unhealthy" trains people to ignore the surface.

See [two-watches.md](two-watches.md) for how to read each one, and
[honesty-matrix.md](honesty-matrix.md) for exactly how much of this is running
today versus designed. The short version of that second one: the attestation and
the health surface are built; the peer-synchronisation engine is not.

## And it needs a lie detector

Listening to your peers means your peers can lie to you. Signed attestation
(scenario 3) proves *who* is speaking — necessary, and not sufficient: an
attested node can still report a false clock. So peer readings are combined with
a **trimmed mean** rather than a plain mean, which costs a little accuracy and
removes the ability of a minority to capture the ensemble. Scenario 4 shows one
liar taking the whole fleet three seconds off UTC under a plain mean, and
getting nowhere under a trimmed one.

## Where to go next

- Run it: `bin/hello-time` (five of the six scenarios need no fabric at all).
- The ladder of external anchors: [anchor-ladder.md](anchor-ladder.md).
- Where any of this is actually enforced: [enforcement-map.md](enforcement-map.md).
- Putting it in your own service: [wire-it-in.md](wire-it-in.md).

Canonical detail lives in [goatcore](https://github.com/usareur-af/goatcore):
[ADR 1037](https://github.com/usareur-af/goatcore/blob/main/docs/adr/1037-fabric-internal-time-synchronization-first.md) (the inversion),
[`docs/design/universal-ntp-hygiene.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/universal-ntp-hygiene.md) (the cross-plane policy),
[`docs/design/ntp-strategy.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/ntp-strategy.md) (anchor acquisition), and
[`docs/design/time-hygiene-trusted-time.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/time-hygiene-trusted-time.md) (the long-form explainer this repo is
the runnable companion to).
