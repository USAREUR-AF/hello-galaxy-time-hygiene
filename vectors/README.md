# Vectors

Signed verdicts produced by the **Go signer** in [goatcore](https://github.com/usareur-af/goatcore)
(`ops/time-hygiene/internal/attest`), not by the Python reference in this repo.
That direction matters: a reference checked only against its own output proves
nothing about interoperating with the real system.

Reference instant for the set: **2026-08-19T22:41:03.127401Z**. Validity windows
are five minutes, so evaluated against your clock today every one of these is
expired — which is itself the lesson in scenario 3. Staleness checks in the
scenarios are made against the reference instant so they read the same in two
years.

| file | verdict | what it is for |
|---|---|---|
| `healthy-gnss.json` | healthy, stratum 1, satellite receiver | the good case |
| `healthy-wan-nts.json` | healthy, stratum 2, authenticated network time | the ordinary anchored case |
| `degraded-orphan.json` | degraded, stratum 10 | orphan mode — self-consistent, unanchored, and it looks fine from inside |
| `unknown-unsynced.json` | unknown, stratum 16 | chrony has no usable source; not "slightly wrong", *does not know* |
| `expired-window.json` | healthy, signed two hours before the reference instant | a valid signature over a stale opinion |
| `unattested.json` | healthy, `attested: false` | the honest unattested posture: no signature, not pretending |
| `tampered-rms.json` | healthy, one field mutated after signing | must fail verification |

Regenerating them takes a small Go program against goatcore's
`ops/time-hygiene/internal/attest` and `internal/signer` packages, with
throwaway Ed25519 keys. The scenarios and `bin/hello-time test` need only the
committed files.
