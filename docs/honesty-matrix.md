# Honesty matrix

What in this repo is a built system, what is a faithful reference, what is a
model, and what does not exist yet. Read this before quoting anything here.

## The system

| capability | state | where you can see it |
|---|---|---|
| Per-host clock verdict from chrony (`ntp-health-agent`) | **built** | scenario 1, the VERDICT column |
| Ed25519 signature over the verdict (`ntp-attest-v1`) | **built** | scenario 3, verifying real signed vectors |
| Signed verdicts published on the bus (`ops/time/attest/<host>`) | **built** | scenario 1, the ATTEST column |
| Per-site roll-up (`ops/time/health/<site>`) with 5-state honesty grading | **built** | scenario 1, the STATE column |
| `goat health --domain time` | **built** | scenario 1 |
| `fake-hwclock` + `chrony-presync` cold-boot layers | **built**, on by default in the hygiene role | scenario 6 (the failure and the fix, locally) |
| Admit-fail-safe sidecar gating the management API | **built**, wired into the generic site stand-up | not demonstrated here |
| Two-axis health as a *model* (internal coherence vs UTC confidence) | **adopted** — it is what the docs, the CLI narration and this repo teach | docs/two-watches.md |
| Two-axis health as *two fields on the wire* | **not built** — one verdict field today, and the colour is the UTC-confidence axis | the publisher's own source says so |
| Peer mutual synchronisation engine (gossip coupling) | **not built** — the model is decided, the engine is the large remaining piece | scenarios 4 and 5 model it; nothing runs it |
| Byzantine-robust aggregation over attested peers | **not built**; the tolerable liar fraction is an open item, not a settled number | scenario 4 shows the shape only |
| Anti-spoof for anchors (multi-anchor cross-check) | **not built**, listed as an open item | not demonstrated |
| Per-message `time_quality` envelope (ADR 0514) | **not built** — no message on any goatnet carries it | not demonstrated |

## This repo

| artefact | what it is |
|---|---|
| `vectors/*.json` | **real output of goatcore's Go signer** (`ops/time-hygiene/internal/attest`), not of the reference below. Committed so the reference can be checked against the real thing. |
| `lib/attest.py` | a **faithful reference** implementation of `ntp-attest-v1`. Mirrors the production canonical view field for field; `bin/hello-time test` proves it. |
| `lib/ed25519_ref.py` | a **textbook** pure-Python Ed25519, so nothing here needs a package install. Not constant-time; do not lift it into anything holding a long-lived secret. |
| `lib/verdict.py` | a **faithful reference** of the classification and honesty-grading rules. Mirrored from the production agent and the roll-up. |
| `lib/ensemble.py` | a **model**, and the only place in this repo where that word applies. No network asymmetry, no measurement noise, no churn, and it corrects offset without disciplining frequency. It is evidence about the *shape* of two behaviours, not about achievable synchronisation error. |
| scenario 1 | reads **your own** goatnet; prints an annotated example without one. |
| scenarios 2, 3, 6 | offline, against real signed vectors and real openssl. |
| scenarios 4, 5 | offline, against the model. Both say so in their first paragraph. |

## Two things worth knowing before you demonstrate this

**A small goatnet's roll-up may see one host.** One host cannot disagree with
anyone, so the peer-consensus idea has nothing to work with there. The roll-up
is correct and the sample is thin. Read the `n=` count rather than assuming a
fleet.

**`goat sub` cannot address the `ops/` namespace.** The CLI resolves the first
key segment as a tenant slot alias and fails closed on anything it does not
recognise, so `goat sub 'ops/time/attest/**'` is refused with `no slot aliased
'ops'`. `goat health --domain time` reads the same data through its own
subscriber and works fine. If you find a runbook telling you to `goat sub` an
`ops/` key, that instruction is stale.
