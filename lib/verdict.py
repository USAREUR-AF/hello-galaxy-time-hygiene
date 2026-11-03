"""How a raw clock reading becomes a verdict, and a verdict becomes a colour.

Two separate steps, deliberately kept apart:

  classify()   — the per-host agent's rule, from chrony's tracking data to one
                 of four classes.  Mirrors ops/time-hygiene/internal/state
                 (Classify / ClassifySource) in goatcore.

  host_colour() — the site roll-up's honesty grading, from a verdict plus two
                 facts ABOUT the verdict (is it signed? is it fresh?) to one of
                 five display states.  Mirrors the site roll-up's
                 host_color() rule.

The second step is where the interesting rule lives, and it is the one people
get wrong when they build a status board: **absence of evidence is rendered as
`idle`, never as green.**  A host that has stopped reporting, and a host that
reports but cannot sign what it says, both read UNCONFIRMED.  A board that
shows the last good value, or shows nothing and lets the eye read that as fine,
is lying by omission at precisely the moment it matters.
"""

from __future__ import annotations

#: Classification thresholds, mirrored from the production agent.
#: rms offset is the running RMS of chrony's estimate of its own error.
_HEALTHY_MAX_NS, _HEALTHY_MAX_STRATUM = 1_000_000, 4       # 1 ms
_WARNING_MAX_NS, _WARNING_MAX_STRATUM = 10_000_000, 6      # 10 ms
_DEGRADED_MAX_NS = 100_000_000                             # 100 ms

#: chrony's own signals for "I am not synchronised at all".
_LEAP_UNSYNCHRONISED = 3
_STRATUM_UNREACHABLE = 16
_STRATUM_ORPHAN = 10   # chrony local/orphan mode: the host is quoting itself

GNSS_REF_IDS = {"GPS", "PPS", "GNSS", "GAL", "GLO", "BDS", "GPSDO", "TSIP"}


def classify(stratum: int, leap_status: int, rms_offset_ns: float) -> str:
    """chrony tracking data → healthy | warning | degraded | unknown."""
    rms = abs(rms_offset_ns)
    if leap_status == _LEAP_UNSYNCHRONISED or stratum >= _STRATUM_UNREACHABLE:
        return "unknown"
    if stratum >= _STRATUM_ORPHAN:
        # Orphan mode is the subtle one: the host is perfectly self-consistent
        # and completely unanchored. It looks synchronised from the inside.
        return "degraded"
    if rms <= _HEALTHY_MAX_NS and stratum <= _HEALTHY_MAX_STRATUM:
        return "healthy"
    if rms <= _WARNING_MAX_NS and stratum <= _WARNING_MAX_STRATUM:
        return "warning"
    if rms <= _DEGRADED_MAX_NS:
        return "degraded"
    return "unknown"


def classify_source(ref_id: str, stratum: int) -> str:
    """chrony's reference id + stratum → which anchor tier is actually in use."""
    if stratum >= _STRATUM_UNREACHABLE:
        return "none"
    if stratum >= _STRATUM_ORPHAN:
        return "orphan"
    return "gnss" if ref_id in GNSS_REF_IDS else "wan_nts"


def host_colour(verdict: str, attested: bool, stale: bool) -> str:
    """verdict + (signed? fresh?) → the 5-state honesty signal.

    THE RULE THAT MATTERS IS THE FIRST LINE.  Unattested or stale reads `idle`
    — unconfirmed — regardless of how good the verdict claims to be.  A host
    asserting `healthy` with no signature behind it, or with a signature from
    an hour ago, has told you nothing you can act on.
    """
    if not attested or stale:
        return "idle"
    return {"healthy": "green", "warning": "amber", "degraded": "red"}.get(verdict, "idle")


def overall_colour(host_colours: list[str]) -> str:
    """Worst GROUNDED host, with two distinct kinds of nothing.

    `idle`      — hosts are reporting, but none of them is confirmable.
    `unmetered` — no host has reported at all; the meter itself is dark.

    Collapsing those two into one state is how a monitoring surface ends up
    unable to distinguish "everything is broken" from "I am not looking".
    """
    if not host_colours:
        return "unmetered"
    for worst in ("red", "amber", "green"):
        if worst in host_colours:
            return worst
    return "idle"
