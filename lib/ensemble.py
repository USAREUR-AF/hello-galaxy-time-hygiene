"""A small, deterministic model of the internal-synchronisation idea.

READ THIS FIRST — THIS IS A MODEL, NOT THE PRODUCT.  The gossip-coupling
engine described in ADR 1037 is **designed and not built**.  Nothing in this
file runs on any goatnet.  It exists so the two claims the design rests on can
be checked by anyone with a laptop, in a few seconds, instead of taken on
trust:

  1. Nodes that keep time by listening to EACH OTHER stay ordered relative to
     one another when the outside reference is gone — while nodes that each
     extrapolate their own crystal (per-node holdover, today's posture) drift
     apart exactly then.
  2. How you AVERAGE peer readings decides whether one lying peer can drag the
     whole ensemble.  A plain mean — the accuracy-optimal choice, and the one
     the underlying research uses — is capturable.  A trimmed mean is not.

The simplification is honest and worth naming: this model has no network delay
asymmetry, no measurement noise, and no churn, so it flatters absolute accuracy.
It is not evidence about achievable synchronisation error; it is evidence about
the SHAPE of the two behaviours above, which is what the design turns on.

Units: microseconds throughout.  Time is in seconds.
"""

from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field


@dataclass
class Node:
    """One fabric participant with its own imperfect crystal.

    `offset_us` is signed error against true UTC — the thing no node can see
    directly.  That is the point: a node cannot diagnose its own clock from the
    inside, which is why the design reaches for peers rather than introspection.
    """

    node_id: str
    offset_us: float = 0.0
    skew_ppm: float = 0.0
    anchored: bool = False
    attested: bool = True
    #: A liar reports this constant instead of its real offset. An attested
    #: liar is the interesting adversary: the attestation gate proves WHO is
    #: speaking, never that what they say is true.
    lies_by_us: float | None = None
    rounds_seen: int = 0
    history: list[float] = field(default_factory=list)

    def reported_offset(self) -> float:
        return self.offset_us if self.lies_by_us is None else self.offset_us + self.lies_by_us

    def free_run(self, dt_s: float) -> None:
        self.offset_us += self.skew_ppm * dt_s


def trimmed_mean(xs: list[float], trim: float = 0.25) -> float:
    """Drop the extreme `trim` fraction from each end, then average.

    The Byzantine-resistant aggregator. It costs a little accuracy against a
    plain mean and buys the property that a minority of liars — even attested,
    even coordinated, as long as they stay a minority — cannot move the result
    beyond the honest spread.
    """
    if not xs:
        return 0.0
    xs = sorted(xs)
    k = int(len(xs) * trim)
    kept = xs[k : len(xs) - k] or xs
    return statistics.fmean(kept)


AGGREGATORS = {
    "mean": lambda xs: statistics.fmean(xs) if xs else 0.0,
    "median": lambda xs: statistics.median(xs) if xs else 0.0,
    "trimmed-mean": trimmed_mean,
}


def coupling_for(rounds_seen: int) -> float:
    """Age-adaptive coupling: a newcomer absorbs fast, an established node is stable.

    Without this, a node joining with a wildly wrong clock either takes forever
    to converge (fixed low coupling) or shakes the ensemble on arrival (fixed
    high coupling).
    """
    return max(0.15, 0.85 * (0.82**rounds_seen))


def sync_round(
    nodes: list[Node],
    rng: random.Random,
    *,
    aggregator: str = "trimmed-mean",
    view_size: int = 4,
    anchor_available: bool = True,
    anchor_weight: int = 2,
) -> None:
    """One round of mutual synchronisation, applied synchronously.

    Each node samples a bounded random view of peers (bounded because the
    population is thousands, so "ask everyone" is not on the table), keeps only
    ATTESTED peers, adds the external anchor as an ordinary — if heavily
    weighted — opinion when one is reachable, and steps toward the aggregate.

    Note what the anchor is here: an opinion with weight, not an authority. Lose
    it and the loop is unchanged; the ensemble simply has nothing pulling it
    toward UTC any more.
    """
    agg = AGGREGATORS[aggregator]
    corrections: dict[str, float] = {}
    for node in nodes:
        others = [n for n in nodes if n.node_id != node.node_id and n.attested]
        view = rng.sample(others, min(view_size, len(others)))
        readings = [peer.reported_offset() - node.offset_us for peer in view]
        if anchor_available and node.anchored:
            # "true UTC is at 0" — the anchor tells the node its own error.
            readings.extend([-node.offset_us] * anchor_weight)
        corrections[node.node_id] = agg(readings) * coupling_for(node.rounds_seen)
    for node in nodes:
        node.offset_us += corrections[node.node_id]
        node.rounds_seen += 1


def spread_us(nodes: list[Node]) -> float:
    """Internal coherence, measured: the worst disagreement between any two nodes.

    This is the number that governs whether timestamps from different producers
    can be ordered, correlated and fused. It never mentions UTC.
    """
    honest = [n.offset_us for n in nodes if n.lies_by_us is None]
    return max(honest) - min(honest)


def utc_error_us(nodes: list[Node]) -> float:
    """UTC confidence, measured: mean absolute error against true UTC.

    This is the number that governs certificate and token validity windows and
    any timestamp a human or another cluster will read. It says nothing about
    whether the fabric can order its own events.
    """
    honest = [abs(n.offset_us) for n in nodes if n.lies_by_us is None]
    return statistics.fmean(honest)


def make_fleet(
    n: int,
    rng: random.Random,
    *,
    anchored: int = 2,
    spread_us_initial: float = 4000.0,
    skew_ppm_range: tuple[float, float] = (-25.0, 25.0),
) -> list[Node]:
    """A fleet of `n` nodes with realistic-ish crystals.

    ±25 ppm is an ordinary commercial oscillator: about 2 seconds of drift per
    day, per node, in its own direction. That number is why per-node holdover
    does not hold a fabric together.
    """
    fleet = []
    for i in range(n):
        fleet.append(
            Node(
                node_id=f"node-{i:02d}",
                offset_us=rng.uniform(-spread_us_initial, spread_us_initial),
                skew_ppm=rng.uniform(*skew_ppm_range),
                anchored=i < anchored,
            )
        )
    return fleet
