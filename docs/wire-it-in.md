# Wiring this into your own service

A checklist for a service that publishes to the fabric. Ordered by how much
trouble skipping it causes.

### 1. Decide honestly whether you are a publisher

The time precondition applies to anything that **publishes**. Pure subscribers
are exempt — and are much rarer than they sound. A last-seen update, an audit
event, a certificate-expiry assertion, a health beat: all publishing. Assume you
are a publisher unless you have explicitly established otherwise.

### 2. Stamp with the producer's clock, and say which clock that was

Consumers order and correlate by producer timestamp. Two rules:

- The timestamp belongs to the **producer**, not to whatever relayed or stored
  it. A receive-time stamp masquerading as an observation time destroys
  ordering at the first hop.
- Where you have it, carry the *quality* alongside the value. The
  fabric-wide inline envelope for this is designed and not built (ADR 0514), so
  today this means: do not throw away what your own stack knows about its clock,
  and do not let a self-clocking source and a satellite-locked one become
  indistinguishable in your schema.

### 3. Read the two axes separately, and gate on the right one

If your service refuses to work when time is imperfect, be specific about which
imperfection:

- ordering, fusion, correlation, last-write-wins → gate on **internal coherence**
- certificate, token and setup-key validity; timestamps leaving the fabric →
  gate on **UTC confidence**

Gating tactical publishing on UTC confidence is the specific mistake this whole
model exists to prevent: it takes your service offline at the denied edge, which
is when it was supposed to matter.

### 4. Fail closed, and say which way you failed

If you cannot reach the time-health signal, treat that as a rejection, not a
pass. An unreachable agent and a host hiding a bad clock look identical from
outside, and you must assume the worse one.

Then report it as its own state. "I could not check" is not "checked and bad",
and it is certainly not "checked and fine".

### 5. Never render absence as health

If your service has a status surface, copy the five-state grading rather than
inventing a three-state one:

- unattested → `idle`, never green
- stale → `idle`, never the last good value
- nothing reporting at all → `unmetered`, which is a different fact from `idle`

`lib/verdict.py` in this repo is a ~90-line reference for exactly this.

### 6. If you verify attestations, check the window too

`Verify` and `Expired` are two calls because they are two failure modes.
Checking only the signature accepts a four-hour-old opinion; checking only the
window accepts a forgery. And carry timestamps as strings — see
[attestation.md](attestation.md) for the two ways verifiers break themselves.

### 7. On hardware without a battery-backed clock, settle the clock before you start

Not "alert if the clock is wrong at startup" — a boot **ordering** dependency.
A service that starts before the clock is settled can cache a wrong now, write
records stamped in the wrong era, or judge a fresh credential expired. Scenario
6 shows the failure and the two layers that close it.
