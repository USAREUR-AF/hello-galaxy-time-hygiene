# The two watches

One clock reading, two questions, two different consequences.

## The questions

**Internal coherence** — is this node in step with the rest of the fabric,
within a bounded error? Answerable peer-to-peer with no external reference, so
it survives the denied edge. This is what event ordering, fusion and correlation,
and multi-master last-write-wins actually require; last-write-wins is correct
when the *writers* agree with each other, which does not involve UTC.

**UTC confidence** — how well is the ensemble anchored to true UTC, and how
recently? Required for certificate, token and setup-key validity windows, and
for any timestamp that leaves the fabric to reach another cluster or a person.
Not required to order data.

## Reading the combinations

| internal coherence | UTC confidence | what it means | publish tactical data? | mint or check a certificate? |
|---|---|---|---|---|
| good | good | fully anchored, everything available | yes | yes |
| good | decaying | **the normal denied-edge state** | yes | with care — the window may be judged wrongly |
| good | unknown | long-denied, still internally ordered | yes | no |
| poor | good | each node UTC-correct, mutually disordered — the worst case, and the one a single-verdict board renders green | no | yes |
| poor | unknown | nothing to stand on | no | no |

The fourth row is why one verdict is not enough. Every node individually
passing a UTC check while disagreeing with each other is a fabric that cannot
order its own events — and a board that only asks "is each clock right?" shows
it as fine.

## What the surface reports today

`goat health --domain time` renders a per-host table with a five-state colour,
the per-host verdict, offset, stratum, whether a satellite receiver is
contributing, and how old the newest signed attestation is. Scenario 1 walks a
reading column by column.

**The colour today is the UTC-confidence axis only.** It is derived from the
per-host chrony verdict. Internal coherence has no field on the wire yet,
because the engine that would measure it is not built. The publisher's own
source code says so; this repo does not soften it. What exists today is the
two-axis *model*, the honesty grading, and a surface shaped to carry the second
reading when there is one to carry.

## The five states, and why five

`green` `amber` `red` are grades of a *grounded* reading — a signed, fresh
verdict the surface can stand behind.

`idle` means UNCONFIRMED: hosts are reporting, but nothing about them is
confirmable — unattested, or stale, or a verdict of `unknown`.

`unmetered` means no host has reported at all: the meter itself is dark.

The last two are separate on purpose. Collapsing them loses the ability to tell
a broken fleet from a broken dashboard, which is the exact confusion an outage
produces. Scenario 2 exercises every state.
