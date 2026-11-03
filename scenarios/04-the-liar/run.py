#!/usr/bin/env python3
"""Scenario 4 — one attested liar, two averaging rules, two different fabrics.

MODEL, NOT PRODUCT. The mutual-synchronisation engine this exercises is
designed and not built (ADR 1037). Nothing here touches a goatnet. What it
shows is why the aggregation rule is a security decision rather than a numerical
one — the reason the design departs from the research it is based on.
"""

import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib import narrate as n  # noqa: E402
from lib.ensemble import Node, make_fleet, spread_us, sync_round, utc_error_us  # noqa: E402

ROUNDS = 40
SEED = 7
LIE_US = 5_000_000  # the liar claims to be five seconds ahead of where it is


def run(aggregator: str):
    rng = random.Random(SEED)
    nodes = make_fleet(9, rng, anchored=2)
    nodes.append(
        Node(
            node_id="liar-01",
            offset_us=0.0,
            skew_ppm=0.0,
            anchored=False,
            attested=True,          # <- it passes the attestation gate
            lies_by_us=LIE_US,
        )
    )
    for _ in range(ROUNDS):
        sync_round(nodes, rng, aggregator=aggregator, anchor_available=True)
    return spread_us(nodes), utc_error_us(nodes)


def main():
    n.title("Scenario 4 — the attested liar")

    n.step(1, "The setup.")
    print()
    print("   Ten participants. Nine honest, each with an ordinary imperfect")
    print("   crystal; two of the nine can currently see an external anchor. The")
    print("   tenth is enrolled, attested, and reports a clock five seconds away")
    print("   from where it really is.")
    print()
    print("   Note what the attestation did and did not do. It proved WHO was")
    print("   speaking. It has nothing to say about whether the content is true.")
    print("   Signature checking is not a truth oracle, and a design that leans on")
    print("   it as one has an unguarded door.")

    n.step(2, f"Run {ROUNDS} rounds of mutual sync under three averaging rules.")
    print()
    print(f"   {'RULE':<14} {'SPREAD (honest nodes)':>22} {'ERROR vs UTC':>18}")
    print(f"   {'-'*14} {'-'*22} {'-'*18}")
    results = {}
    for agg in ("mean", "median", "trimmed-mean"):
        spread, err = run(agg)
        results[agg] = (spread, err)
        paint = n.red if spread > 1000 else n.green
        row = f"{agg:<14} {spread:>19,.0f} µs {err:>15,.0f} µs"
        print("   " + paint(row))

    n.step(3, "What happened.")
    print()
    mean_s, mean_e = results["mean"]
    trim_s, trim_e = results["trimmed-mean"]
    print(f"   Plain mean:   the ensemble is dragged {mean_e/1e6:.1f} s off UTC and the")
    print(f"                 honest nodes end up {mean_s/1e3:,.0f} ms apart from each other.")
    print(f"   Trimmed mean: {trim_e/1000:.1f} ms off UTC, {trim_s/1000:.2f} ms apart. The liar is")
    print("                 outvoted every round and never gets purchase.")
    print()
    print("   A mean is the accuracy-optimal estimator when everyone is honest,")
    print("   and it is the one the underlying gossip-synchronisation research")
    print("   uses — that research explicitly does not model an adversary. On a")
    print("   fabric whose threat model includes a captured node, the same choice")
    print("   is a single-node capture of fabric time. Trimming the extremes costs")
    print("   a little accuracy and removes the capture.")

    n.step(4, "The bound, stated honestly.")
    print()
    print("   Trimming survives a MINORITY of liars. It is not a guarantee against")
    print("   a coordinated majority, and the exact tolerable fraction — how much")
    print("   trim, against how many colluding attested peers, with what residual")
    print("   error — is an open item in ADR 1037, not a settled number. This")
    print("   scenario shows the shape of the difference. It is not a proof of the")
    print("   bound, and this model is generous: no network asymmetry, no")
    print("   measurement noise, no churn.")

    ok = mean_s > 10 * trim_s
    print()
    n.verdict(ok, "a plain mean is capturable by one attested liar; a trimmed mean is not")
    print()
    print(n.dim("   Next: scenarios/05-free-run-together"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
