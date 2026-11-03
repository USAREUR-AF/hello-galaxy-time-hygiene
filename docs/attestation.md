# The signed verdict

A host cannot verify its own clock from the inside. That is not a gap in the
tooling; it is the shape of the problem. A host with a wrong clock, or a
compromised one, reports confidently that everything is fine, and every internal
check it runs agrees with it.

The way out is other hosts — which immediately raises the question of why you
would believe *them*. Hence a signature.

## What is signed, and what is deliberately not

`ntp-attest-v1` covers exactly nine fields, in this order:

```
alg · host_id · ntp_class_str · selected_source · stratum · ref_id
    · rms_offset_ns · last_updated_utc · valid_until
```

The verdict document on the wire carries more than that — a drift model,
instantaneous frequency, leap status. Those are outside the signature on
purpose: they move between the moment of signing and the moment of reading, so
covering them would make honest attestations fail for no reason. **What is
signed is the verdict and the time it was made** — the load-bearing claim for
peer consensus and for gating.

`alg` versions the covered set. A reader that does not recognise the algorithm
must treat the attestation as **unverifiable**, which is not the same as
**invalid**. Conflating those two turns every future widening of the field set
into a fleet-wide false alarm.

## What a valid signature proves, and what it does not

It proves whoever holds that key made this claim. It does **not** prove the key
belongs to that host.

Key authenticity is rooted elsewhere: a host's public attestation key travels in
its offline-CA-signed enrollment bundle, so the chain ends at a certificate
authority whose private half lives on no network-reachable machine. A management
host compromise cannot rewrite that binding.

Hosts enrolled without such a bundle have no CA-signed key binding. They publish
honestly **unattested** — accepted for local telemetry, excluded from consensus.
Unattested is a posture, not an error, and it is rendered `idle`, never green.

## Two failure modes, two checks

A signature that verifies over a verdict from four hours ago is a valid
signature over a stale opinion. Staleness and forgery are different failures and
each is silent if you only check the other:

- signature only → accepts an old reading as current
- window only → accepts anything a forger cares to write

The production interface splits them into two calls, `Verify` and `Expired`, so
neither can be skipped by accident. `valid_until` is *inside* the signed view,
so a relay cannot extend the life of a verdict it is carrying — freshness is the
signer's claim, not the courier's.

The site roll-up goes one step further: it measures staleness against its own
**local receive time**, not against the timestamps inside the verdict. Trusting
a clock's self-reported timestamp to decide whether its report is fresh is
circular — that clock is the thing being measured.

## Determinism, which is where verifiers actually break

A signature is over bytes. Rebuild those bytes even slightly differently and
every honest attestation fails. Two rules, both easy to get wrong:

**Carry timestamps verbatim.** The signer writes RFC 3339 at nanosecond
precision with trailing zeros trimmed. Most languages' datetime types hold
microseconds. Parse and re-emit and you have silently truncated the string you
are about to hash. Never re-format a timestamp on the way to verification.

**Match the serialiser, do not improve on it.** The production signer is Go's
`encoding/json`: compact separators, fields in *declaration* order (not
alphabetical), raw UTF-8, with `<`, `>` and `&` escaped. Sorting the keys "to be
canonical" produces different bytes and a dead signature. Scenario 3 prints the
exact offset at which the two diverge.

## Reading it in this repo

`lib/attest.py` is the readable reference — sign view, byte form, verify,
expiry — with the traps documented in place. `lib/ed25519_ref.py` is a bundled
pure-Python Ed25519 so nothing here needs a package install.

The vectors in `vectors/` were produced by the production Go signer, not by the
reference. `bin/hello-time test` verifies them on both backends. A reference
checked only against its own output proves nothing about interoperating with the
real system, which is the point of doing it this way round.
