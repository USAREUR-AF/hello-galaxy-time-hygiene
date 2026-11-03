#!/usr/bin/env python3
"""The cross-check that keeps this repo honest.

Every vector in ../vectors/ was signed by goatcore's production Go
signer (ops/time-hygiene/internal/attest). This test verifies them with the
Python reference in ../lib/attest.py, on BOTH Ed25519 backends. If the
reference ever drifts from the production canonical view — a re-ordered field,
a re-formatted timestamp, a different escaping rule — these assertions fail.

That is the whole reason the vectors come from the real signer rather than from
the reference itself: a reference checked only against its own output proves
nothing about interoperating with the real system.
"""

import base64
import json
import pathlib
import sys
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from lib import attest, ed25519_ref  # noqa: E402
from lib.verdict import classify, classify_source, host_colour, overall_colour  # noqa: E402

VECTORS = ROOT / "vectors"
REFERENCE_INSTANT = datetime(2026, 8, 19, 22, 41, 3, 127401, tzinfo=timezone.utc)

SHOULD_VERIFY = ["healthy-gnss", "healthy-wan-nts", "degraded-orphan",
                 "unknown-unsynced", "expired-window"]

failures = []


def check(cond, label):
    print(f"  {'ok  ' if cond else 'FAIL'}  {label}")
    if not cond:
        failures.append(label)


def load(name):
    return json.loads((VECTORS / f"{name}.json").read_text())


print(f"backend in use: {attest.backend_name()}")

print("\nproduction-signed vectors verify against the reference")
for name in SHOULD_VERIFY:
    check(attest.verify(load(name)) is True, name)

print("\nthe same vectors verify on the pure-Python backend (no cryptography needed)")
for name in SHOULD_VERIFY:
    v = load(name)
    ok = ed25519_ref.verify(
        base64.b64decode(v["attestation_pubkey"]),
        attest.signing_bytes(v),
        base64.b64decode(v["signature"]),
    )
    check(ok is True, name)

print("\nnegative cases")
check(attest.verify(load("tampered-rms")) is False, "a mutated field fails the signature")
check(attest.verify(load("unattested")) is False, "unattested verifies False, raises nothing")
try:
    bad = load("healthy-gnss") | {"attestation_alg": "ntp-attest-v99"}
    attest.verify(bad)
    check(False, "an unknown alg raises Unverifiable")
except attest.Unverifiable:
    check(True, "an unknown alg raises Unverifiable (not a signature failure)")

print("\nvalidity windows, evaluated at the vector set's reference instant")
check(attest.expired(load("healthy-gnss"), REFERENCE_INSTANT) is False, "fresh verdict is open")
check(attest.expired(load("expired-window"), REFERENCE_INSTANT) is True, "old verdict is closed")

print("\nclassification mirrors the production agent")
check(classify(1, 0, 187_000) == "healthy", "1 ms at stratum 1 → healthy")
check(classify(3, 0, 9_000_000) == "warning", "9 ms at stratum 3 → warning")
check(classify(10, 0, 41_000_000) == "degraded", "orphan mode → degraded, never healthy")
check(classify(16, 0, 0) == "unknown", "stratum 16 → unknown")
check(classify(2, 3, 0) == "unknown", "chrony leap=3 (unsynchronised) → unknown")
check(classify_source("GPS", 1) == "gnss", "GPS refid → gnss")
check(classify_source("A29FC801", 2) == "wan_nts", "an address-shaped refid → network time")

print("\nhonesty grading: absence never renders as health")
check(host_colour("healthy", attested=False, stale=False) == "idle", "unattested healthy → idle")
check(host_colour("healthy", attested=True, stale=True) == "idle", "stale healthy → idle")
check(host_colour("healthy", attested=True, stale=False) == "green", "signed and fresh → green")
check(overall_colour([]) == "unmetered", "no host reporting → unmetered, not idle")
check(overall_colour(["idle", "idle"]) == "idle", "reporting but unconfirmable → idle")
check(overall_colour(["green", "red", "idle"]) == "red", "worst grounded host wins")

print()
if failures:
    print(f"{len(failures)} FAILED: {', '.join(failures)}")
    sys.exit(1)
print("all checks passed")
