#!/usr/bin/env python3
"""Scenario 2 — a status board that cannot lie by omission.

Runs offline against the signed verdicts in ../../vectors/, which were produced
by the production Go signer.

The claim under test: on this surface, the absence of evidence is never
rendered as health. A host that stops reporting, and a host that reports
without signing, both read UNCONFIRMED — not green, and not the last good value.
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib import narrate as n  # noqa: E402
from lib.verdict import classify, classify_source, host_colour, overall_colour  # noqa: E402

VECTORS = ROOT / "vectors"

# The instant the vector set was signed at. Staleness is measured against a
# fixed reference so this scenario reads the same today and in two years.
REFERENCE_INSTANT = "2026-08-19T22:41:03.127401Z"
STALE_AFTER_S = 90  # three heartbeats, the production default


def load(name):
    return json.loads((VECTORS / f"{name}.json").read_text())


def main():
    n.title("Scenario 2 — absence of evidence is not evidence of health")

    n.step(1, "Six hosts report. Same board, same rules, six different truths.")
    print()
    print(f"   {'HOST':<20} {'CLASS':<9} {'SOURCE':<9} {'SIGNED':<7} {'FRESH':<6} {'BOARD'}")
    print(f"   {'-'*20} {'-'*9} {'-'*9} {'-'*7} {'-'*6} {'-'*5}")

    cases = [
        ("healthy-gnss", False, "anchored to a satellite receiver"),
        ("healthy-wan-nts", False, "anchored to authenticated network time"),
        ("degraded-orphan", False, "quoting itself as its own reference"),
        ("unknown-unsynced", False, "chrony has no usable source at all"),
        ("unattested", False, "says healthy; cannot sign that it said so"),
        ("healthy-gnss", True, "was healthy; has not been heard from since"),
    ]
    colours = []
    for name, force_stale, gloss in cases:
        v = load(name)
        cls = classify(v["stratum"], v["leap_status"], v["rms_offset_ns"])
        src = classify_source(v["ref_id"], v["stratum"])
        signed = bool(v.get("attested"))
        colour = host_colour(cls, signed, force_stale)
        colours.append(colour)
        host = v["host_id"] + ("*" if force_stale else "")
        paint = {"green": n.green, "amber": n.amber, "red": n.red}.get(colour, n.dim)
        print(
            f"   {host:<20} {cls:<9} {src:<9} {'yes' if signed else 'no':<7} "
            f"{'no' if force_stale else 'yes':<6} {paint(colour)}"
        )
        n.note(f"  └ {gloss}")

    n.note("")
    n.note("* same signed verdict as row 1 — only its freshness differs.")

    n.step(2, "Two of those rows claim to be healthy. Neither is shown as green.")
    print()
    print("   The unattested host and the stale host both read idle. Nothing about")
    print("   their claimed class changed; what changed is whether anyone can stand")
    print("   behind it. A board that renders either as green has converted 'I do")
    print("   not know' into 'fine', which is the failure that gets acted on.")

    n.step(3, "The site roll-up keeps two different kinds of nothing apart.")
    print()
    for label, cs in [
        ("hosts reporting, one degraded", colours),
        ("hosts reporting, none confirmable", ["idle", "idle", "idle"]),
        ("no host has reported at all", []),
    ]:
        print(f"   {label:<34} → {overall_colour(cs)}")
    print()
    print("   idle and unmetered are not the same fact. idle says the hosts are")
    print("   there and unconfirmable; unmetered says the meter is dark. Collapse")
    print("   them and you lose the ability to tell a broken fleet from a broken")
    print("   dashboard — which is exactly the confusion an outage produces.")

    ok = (
        host_colour("healthy", False, False) == "idle"
        and host_colour("healthy", True, True) == "idle"
        and overall_colour([]) == "unmetered"
    )
    print()
    n.verdict(ok, "unattested → idle, stale → idle, empty → unmetered")
    print()
    print(n.dim("   Next: scenarios/03-verify-an-attestation"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
