# Hello Galaxy — time hygiene

**On a fabric with no central anything, what you need is that participants agree
with *each other* about time — not that each of them is right about UTC.**

This is a teaching walkthrough with six runnable scenarios. Five of them need
nothing but Python and openssl; one reads your own goatnet. It answers one question
completely:

> When satellite navigation is jammed and the link out is cut — the *normal*
> condition at the tactical edge, not the exception — how does a brokerless mesh
> keep its data orderable, keep a liar from dragging everyone's clock, and tell
> you honestly when it does not know what time it is?

The answer has three moving parts. Participants keep time by **listening to each
other** rather than copying a master. External references are demoted from
foundation to **opportunistic anchor**. And health splits into **two independent
readings** — internal coherence, which survives the denied edge, and UTC
confidence, which honestly decays — because they govern completely different
decisions.

Start with [`docs/00-agree-not-be-right.md`](docs/00-agree-not-be-right.md).
It is the whole mental model in two minutes.

---

## Read this before quoting anything here

Some of what follows is built in goat; some of it is designed and not built. The line between them is not blurred anywhere in this repo, and it is
drawn in one place: [`docs/honesty-matrix.md`](docs/honesty-matrix.md).

The short version:

| | |
|---|---|
| **Running today** | the per-host clock verdict, its Ed25519 signature, both published on the bus, the per-site roll-up with five-state honesty grading, and `goat health --domain time` — built in [goatcore](https://github.com/usareur-af/goatcore) (`ops/time-hygiene`, `goat` CLI) |
| **Adopted as the model** | two-axis health, and the demotion of external references to anchors — this is what the docs, the CLI narration and this repo teach |
| **Not built** | the peer mutual-synchronisation engine itself, two-axis health as two fields on the wire, the per-message time-quality envelope, and anchor anti-spoofing |

Scenarios 4 and 5 model the unbuilt engine and say so in their first paragraph.
Everything else runs against real signatures, real openssl, or your own goatnet.

---

## Run it

```bash
git clone https://github.com/usareur-af/hello-galaxy-time-hygiene
cd hello-galaxy-time-hygiene

bin/hello-time            # all six, in order
bin/hello-time offline    # the five that need no fabric
bin/hello-time 3          # just scenario 3
bin/hello-time test       # check the reference against the production vectors
```

No install step. `cryptography` is used for Ed25519 when it happens to be
present; otherwise a bundled pure-Python implementation
(`lib/ed25519_ref.py`) takes over and the same tests pass either way.

Scenario 1 is the only step that needs a goatnet: the `goat` CLI and a
goatnet you can reach. If you do not have one, goatcore's
[goatlite quickstart](https://github.com/usareur-af/goatcore/blob/main/docs/tutorials/00-goatlite.md)
stands one up on a single machine. Without a goatnet, scenario 1 prints an
annotated example of its output instead.

```bash
GOAT_CONTEXT=<your-goatnet> bin/hello-time 1   # runs: goat --context <your-goatnet> health --domain time
```

---

## The six scenarios

| | scenario | needs | what it settles |
|---|---|---|---|
| 1 | [two watches](scenarios/01-two-watches/) | `goat` + your goatnet | how to read the time surface, column by column — and what it is not telling you yet |
| 2 | [absence is not health](scenarios/02-absence-is-not-health/) | nothing | two hosts claim to be healthy; neither shows green. Why `idle` and `unmetered` are different facts |
| 3 | [verify an attestation](scenarios/03-verify-an-attestation/) | nothing | check a **production-signed** verdict with a readable reference, then break it five ways |
| 4 | [the liar](scenarios/04-the-liar/) | nothing | one attested liar captures the fleet under a plain mean and gets nowhere under a trimmed one |
| 5 | [free-run together](scenarios/05-free-run-together/) | nothing | the anchor is cut: mutual sync holds ordering flat, per-node holdover comes apart |
| 6 | [cold boot 1970](scenarios/06-cold-boot-1970/) | `openssl` | a board with no battery-backed clock cannot rejoin its own mesh, and the two layers that fix it |

---

## The ideas, in the order they build

**Agreement beats correctness.** Two nodes four seconds off in the same
direction order their events perfectly. Two nodes each within a millisecond of
UTC but disagreeing by two seconds cannot. Ordering, fusion, correlation and
last-write-wins all need the first property; only certificates and outward-facing
timestamps need the second.
→ [`docs/00-agree-not-be-right.md`](docs/00-agree-not-be-right.md)

**So there are two watches, not one verdict.** Internal coherence governs fabric
participation and survives the denied edge. UTC confidence governs validity
windows and decays honestly when nothing is anchoring the ensemble. A node that
is coherent but does not know UTC is the *normal, correct* denied-edge state and
a fully valid publisher.
→ [`docs/two-watches.md`](docs/two-watches.md)

**External references are anchors, not authorities.** Satellite receivers and
authenticated network time pull the ensemble toward UTC when reachable and are
absent otherwise. The best rung of the ladder is also the most attackable, which
is exactly why nothing is allowed to depend on it.
→ [`docs/anchor-ladder.md`](docs/anchor-ladder.md)

**A host cannot verify its own clock, so it signs its verdict for others.** Nine
fields, versioned, with the validity window inside the signature so a relay
cannot extend it. A valid signature proves who spoke — never that the content is
true, and never that the key belongs to that host.
→ [`docs/attestation.md`](docs/attestation.md)

**Listening to peers means peers can lie, so the averaging rule is a security
decision.** A trimmed mean costs a little accuracy and removes a minority's
ability to capture the ensemble.
→ scenario 4

**None of it matters unless something acts on it — and most of what would act
is not built yet.** Reveal before enforce is deliberate; it is also the honest
current position.
→ [`docs/enforcement-map.md`](docs/enforcement-map.md)

**Putting it in your own service.** Seven checks, ordered by how much trouble
skipping them causes.
→ [`docs/wire-it-in.md`](docs/wire-it-in.md)

---

## What is in here

```
docs/          the ideas, in reading order
scenarios/     six runnable acts, each with its own README
lib/           readable reference implementations — attest, verdict, ensemble
vectors/       verdicts signed by goatcore's Go signer, not by lib/
tests/         the cross-check that keeps lib/ honest against vectors/
```

`lib/attest.py` and `lib/verdict.py` are faithful mirrors of the production Go
code, and `bin/hello-time test` proves it by verifying signatures the real
signer produced. `lib/ensemble.py` is the one thing here that is a model, and it
says so at the top of the file.

---

## Where the canonical detail lives

This repo is the runnable companion to the long-form explainer, not a
replacement for it. In [goatcore](https://github.com/usareur-af/goatcore):

- [ADR 1037](https://github.com/usareur-af/goatcore/blob/main/docs/adr/1037-fabric-internal-time-synchronization-first.md) — the inversion: internal synchronisation first, external
  reference as an anchor, two-axis health, attestation-gated coupling
- [`docs/design/universal-ntp-hygiene.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/universal-ntp-hygiene.md) — the cross-plane policy, including
  the enforcement table scenario-by-scenario references here
- [`docs/design/ntp-strategy.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/ntp-strategy.md) — anchor acquisition, the tiers
- [`docs/design/time-hygiene-trusted-time.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/time-hygiene-trusted-time.md) — the long-form explainer
- [`docs/design/time-quality-attestation.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/time-quality-attestation.md) + [ADR 0514](https://github.com/usareur-af/goatcore/blob/main/docs/adr/0514-time-quality-attestation.md) — the per-message
  envelope, designed and not built
- [`docs/design/environment-health-surface.md`](https://github.com/usareur-af/goatcore/blob/main/docs/design/environment-health-surface.md) + [ADR 1036](https://github.com/usareur-af/goatcore/blob/main/docs/adr/1036-environment-health-surface.md) — the surface the
  time domain publishes into
- [`ops/time-hygiene`](https://github.com/usareur-af/goatcore/blob/main/ops/time-hygiene) — the per-host agent and the signer that produced `vectors/`

---

## The rest of the series

Each Hello Galaxy is a small, self-contained, runnable example of best practice
in one dimension — the way "hello, world" is the smallest honest example of a
language. See [`usareur-af`](https://github.com/orgs/usareur-af/repositories?q=hello-galaxy)
for the others.

## Licence

Apache License 2.0 ([LICENSE](LICENSE)). See also [NOTICE](NOTICE),
[CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
