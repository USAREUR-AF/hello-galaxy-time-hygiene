#!/usr/bin/env python3
"""Scenario 3 — check a signature over a real production-signed verdict.

Offline. The vectors in ../../vectors/ were produced by goatcore's
own Go signer (ops/time-hygiene/internal/attest). The verifier here is the
readable Python reference in ../../lib/attest.py. If the two ever disagree
about a byte, this scenario fails — which is the point of shipping vectors from
the real signer rather than from the reference itself.
"""

import copy
import json
import pathlib
import sys
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib import attest  # noqa: E402
from lib import narrate as n  # noqa: E402

VECTORS = ROOT / "vectors"
REFERENCE_INSTANT = datetime(2026, 8, 19, 22, 41, 3, 127401, tzinfo=timezone.utc)


def load(name):
    return json.loads((VECTORS / f"{name}.json").read_text())


def main():
    n.title("Scenario 3 — verifying a signed time verdict")
    print(f"   backend: {attest.backend_name()}")

    v = load("healthy-gnss")

    n.step(1, "The bytes that are actually signed.")
    print()
    print("   " + attest.signing_bytes(v).decode())
    print()
    print("   That is the whole signed view — nine fields, in that order. The")
    print("   verdict document on the wire carries more (drift model, frequency,")
    print("   leap status); those are deliberately outside the signature because")
    print("   they move between signing and reading. What is signed is the verdict")
    print("   and the time it was made.")

    n.step(2, "It verifies.")
    ok_real = attest.verify(v)
    n.verdict(ok_real, f"{v['host_id']} — signature valid over its embedded key")
    print()
    print("   Read that claim precisely: it proves whoever holds that key said")
    print("   this. It does NOT prove the key belongs to that host. Key")
    print("   authenticity is rooted separately — the host's public attestation")
    print("   key travels in its offline-CA-signed enrollment bundle, so the chain")
    print("   ends at a CA whose private half is on no network-reachable machine.")
    print("   A verifier that stops at this step has checked a self-signed note.")

    n.step(3, "Change one number and it stops verifying.")
    print()
    results = []
    for field, new in [
        ("ntp_class_str", "degraded"),
        ("host_id", "some-other-host"),
        ("rms_offset_ns", 1),
        ("stratum", 3),
        ("valid_until", "2027-01-01T00:00:00Z"),
    ]:
        t = copy.deepcopy(v)
        was = t[field]
        t[field] = new
        bad = attest.verify(t)
        results.append(not bad)
        print(f"   {field:<16} {str(was)[:24]:<26} → {str(new)[:24]:<26} verify={n.red('False') if not bad else n.green('True')}")
    print()
    print("   The last row is the one worth pausing on. `valid_until` is inside")
    print("   the signed view, so a relay cannot extend the life of a verdict it")
    print("   is carrying. Freshness is the signer's claim, not the courier's.")

    n.step(4, "A valid signature over a stale verdict is the normal case.")
    print()
    for name in ("healthy-gnss", "expired-window"):
        w = load(name)
        sig_ok = attest.verify(w)
        stale = attest.expired(w, REFERENCE_INSTANT)
        usable = sig_ok and not stale
        print(
            f"   {name:<16} signature={'ok' if sig_ok else 'BAD':<4} "
            f"window={'closed' if stale else 'open':<7} "
            f"→ {(n.green('usable') if usable else n.red('not usable'))}"
        )
    real_now = datetime.now(timezone.utc)
    both_now = [attest.expired(load(x), real_now) for x in ("healthy-gnss", "expired-window")]
    print()
    print(f"   Evaluated at the vector set's reference instant ({REFERENCE_INSTANT:%Y-%m-%d %H:%M}Z).")
    print(f"   Evaluated at your clock right now, both are expired: {both_now}.")
    print()
    print("   Both failure modes are silent in opposite directions if you check")
    print("   only one. Signature-only accepts a four-hour-old opinion about a")
    print("   clock. Window-only accepts anything a forger cares to write. The")
    print("   production verifier splits them into two calls — Verify and Expired")
    print("   — so neither can be skipped by accident.")

    n.step(5, "Unattested is a posture, not an error.")
    u = load("unattested")
    print()
    print(f"   {u['host_id']} publishes attested=false: no signature, no key, and")
    print("   an advisory validity window all the same. That is the honest")
    print("   unattested-publisher posture — the host is not pretending. Consumers")
    print("   take its telemetry and exclude it from consensus.")
    n.verdict(attest.verify(u) is False, "verify(unattested) is False, and raises nothing")

    n.step(6, "An algorithm you do not recognise is unverifiable, not invalid.")
    future = copy.deepcopy(v)
    future["attestation_alg"] = "ntp-attest-v2"
    try:
        attest.verify(future)
        got = "returned a verdict"
    except attest.Unverifiable as exc:
        got = f"Unverifiable — {exc}"
    print()
    print(f"   {got}")
    print()
    print("   That distinction is what lets the signed field set widen later. A")
    print("   reader that treats an unknown alg as a failed signature turns every")
    print("   future upgrade into a fleet-wide false alarm.")

    n.step(7, "The two ways a verifier breaks itself.")
    print()
    print("   Both are about rebuilding the signed bytes differently from the signer:")
    print()
    print("   a) Re-formatting the timestamps. The wire carries nanoseconds; most")
    print("      languages' datetime types hold microseconds. Parse and re-emit and")
    print("      you have silently truncated the string you are about to hash.")
    print("      Carry it verbatim. lib/attest.py never parses a timestamp except")
    print("      to compare it.")
    print("   b) Re-ordering or re-spacing the JSON. The production signer is Go's")
    print("      encoding/json: compact, declaration order, raw UTF-8, with <, > and")
    print("      & escaped. Sort the keys 'to be canonical' and every signature fails.")
    print()
    demo = attest.signing_bytes(v)
    resorted = json.dumps(
        json.loads(demo.decode()), separators=(",", ":"), sort_keys=True
    ).encode()
    i = next((k for k in range(min(len(demo), len(resorted))) if demo[k] != resorted[k]), 0)
    print(f"   first byte that differs: offset {i} of {len(demo)}")
    print(f"   signer emits        …{demo[i - 18:i + 22].decode()}…")
    print(f"   'canonical' sorting …{resorted[i - 18:i + 22].decode()}…")
    n.verdict(demo != resorted, "same fields, different bytes, dead signature")

    ok = ok_real and all(results) and attest.verify(load("tampered-rms")) is False
    print()
    n.verdict(ok, "production-signed vectors verify; every tamper is caught")
    print()
    print(n.dim("   Next: scenarios/04-the-liar"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
