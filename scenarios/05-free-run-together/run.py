#!/usr/bin/env python3
"""Scenario 5 — the anchor goes away. What survives, and what honestly decays.

MODEL, NOT PRODUCT. The mutual-synchronisation engine is designed and not built
(ADR 1037). The contrast arm — per-node holdover — IS today's posture, which is
what makes the comparison worth running.

The question: when GNSS is jammed and the link out is cut, what exactly is lost?
The answer the design turns on is that TWO different things are at stake and
they fail at different rates. Ordering, correlation and last-write-wins need
participants to agree with EACH OTHER. Certificates, tokens and human-facing
timestamps need agreement with UTC. Only the second one depends on the anchor.
"""

import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from lib import narrate as n  # noqa: E402
from lib.ensemble import make_fleet, spread_us, sync_round, utc_error_us  # noqa: E402

DT_S = 30.0             # one round every 30 s, the production heartbeat
ROUNDS = 240            # two hours
ANCHOR_UNTIL = 60       # anchor reachable for the first 30 minutes
SEED = 11
SAMPLES = (29, 59, 119, 239)


def run(mutual: bool):
    rng = random.Random(SEED)
    nodes = make_fleet(8, rng, anchored=2)
    out = []
    for r in range(ROUNDS):
        anchor = r < ANCHOR_UNTIL
        for node in nodes:
            node.free_run(DT_S)
        if mutual:
            sync_round(nodes, rng, aggregator="trimmed-mean", anchor_available=anchor)
        elif anchor:
            # Today's posture: each anchored node steers ITSELF; unanchored nodes
            # extrapolate their own crystal and answer to nobody.
            for node in nodes:
                if node.anchored:
                    node.offset_us *= 0.15
        if r in SAMPLES:
            out.append(((r + 1) * DT_S / 60, anchor, spread_us(nodes), utc_error_us(nodes)))
    return out


def main():
    n.title("Scenario 5 — free-running together beats free-running apart")

    n.step(1, "Eight nodes, two hours. The anchor is cut at the 30-minute mark.")
    print()
    print("   Two arms, same nodes, same crystals, same seed:")
    print("     mutual sync       — every node steers toward its peers (ADR 1037, not built)")
    print("     per-node holdover — every node extrapolates its own crystal (today)")

    rows = {"mutual sync": run(True), "per-node holdover": run(False)}

    n.step(2, "SPREAD is internal coherence: the worst disagreement between two nodes.")
    print()
    print(f"   {'':<20}{'30 min':>13}{'30 min':>13}{'60 min':>13}{'120 min':>13}")
    print(f"   {'':<20}{'anchored':>13}{'cut':>13}{'cut':>13}{'cut':>13}")
    for label, rr in rows.items():
        cells = "".join(f"{s/1000:>10,.1f} ms" for _, _, s, _ in rr)
        print(f"   {label:<20}{cells}")
    print()
    print("   Mutual sync holds the spread flat once the anchor is gone. Holdover")
    print("   does not: the nodes were never listening to each other, so from the")
    print("   moment the anchor disappears each one walks off in its own direction")
    print("   at its own rate, and the disagreement grows without bound.")
    print()
    print("   This is the specific failure the design exists to fix. Holdover")
    print("   preserves ONE node's time. It does not preserve MUTUAL time, and")
    print("   mutual time is what event ordering, correlation and last-write-wins")
    print("   are made of.")

    n.step(3, "ERROR vs UTC is the other watch, and it is supposed to decay.")
    print()
    print(f"   {'':<20}{'30 min':>13}{'30 min':>13}{'60 min':>13}{'120 min':>13}")
    for label, rr in rows.items():
        cells = "".join(f"{e/1000:>10,.1f} ms" for _, _, _, e in rr)
        print(f"   {label:<20}{cells}")
    print()
    print("   Under mutual sync the ensemble drifts away from UTC together once")
    print("   nothing is anchoring it. That is not a fault to be alarmed on — it is")
    print("   the honest consequence of having no reference, and the reading that")
    print("   should be shown is 'coherent, UTC confidence decaying', not 'unhealthy'.")
    print()
    print("   Concretely, in the mutual-sync arm at the two-hour mark: fusing and")
    print("   ordering data across those nodes is fine. Issuing a certificate whose")
    print("   validity window you expect a distant cluster to honour is not.")

    n.step(4, "What this model does not do.")
    print()
    print("   It corrects offset only, never frequency, so a residual proportional")
    print("   to drift-per-round remains rather than converging toward zero — the")
    print("   flat line above sits at a few milliseconds, not at nothing. A real")
    print("   implementation disciplines frequency as well. There is also no")
    print("   network-delay asymmetry, no measurement noise, and no churn here.")
    print("   Treat the SHAPE as the result — flat versus growing — and take no")
    print("   achievable-synchronisation-error number away from it.")

    m = rows["mutual sync"]
    h = rows["per-node holdover"]
    coherence_holds = m[-1][2] < 2 * m[1][2]
    holdover_diverges = h[-1][2] > 3 * h[1][2]
    utc_decays = m[-1][3] > 2 * m[1][3]
    print()
    n.verdict(coherence_holds, "mutual sync: spread stays bounded after the anchor is cut")
    n.verdict(holdover_diverges, "holdover: spread grows without bound after the same cut")
    n.verdict(utc_decays, "mutual sync: UTC error grows — decaying honestly, not hidden")
    print()
    print(n.dim("   Next: scenarios/06-cold-boot-1970"))
    return 0 if (coherence_holds and holdover_diverges and utc_decays) else 1


if __name__ == "__main__":
    sys.exit(main())
