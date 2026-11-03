# 3 — Verifying a signed time verdict

**Run:** `python3 run.py` (or `bin/hello-time 3`) · **Needs:** nothing
(`cryptography` is used when present; a bundled pure-Python Ed25519 otherwise)

Verifies real verdicts signed by the **production Go signer**, with the readable
Python reference in `lib/attest.py`. Prints the exact bytes that get signed,
then breaks them in five different ways.

Seven steps, and four of them are the point:

- a valid signature proves *who spoke*, not that the key belongs to that host —
  key authenticity is rooted in an offline-CA-signed enrollment bundle
- `valid_until` is *inside* the signed view, so a relay cannot extend a
  verdict's life
- a valid signature over a stale verdict is the common case; signature and
  window are two checks because they are two failure modes
- an unrecognised algorithm is **unverifiable**, not **invalid** — conflating
  them turns every future format widening into a fleet-wide false alarm

The last step shows the two ways a verifier breaks itself: re-formatting the
timestamps, and "helpfully" sorting the JSON keys. It prints the byte offset at
which the second one diverges.

Reference: [../../docs/attestation.md](../../docs/attestation.md).
