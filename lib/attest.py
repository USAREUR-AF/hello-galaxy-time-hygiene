"""ntp-attest-v1 — a readable reference implementation of the signed time verdict.

WHAT THIS IS.  Every host on the fabric runs an agent that decides how good its
own clock is, and then *signs that decision*.  The signature is what lets any
other participant say "host X asserted verdict V, valid until T" without
trusting whoever carried the message.  That is the precondition for peer
consensus and for gating on time at all.

WHAT IT COVERS.  The signature does NOT cover the whole verdict document.  It
covers a fixed, ordered, versioned subset — the `signing view` below:

    alg · host_id · ntp_class_str · selected_source · stratum · ref_id
        · rms_offset_ns · last_updated_utc · valid_until

That is deliberate.  Volatile fields (the drift model, instantaneous frequency,
leap status) move between the moment of signing and the moment of reading, so
including them would make signatures spuriously fail.  What is signed is *the
verdict and the time it was made* — the load-bearing claim.  The `alg` string
versions the covered set, so a future v2 can widen coverage without a silent
mismatch: a reader that does not recognise the alg must treat the attestation
as UNVERIFIABLE, which is not the same as INVALID.

DETERMINISM IS THE WHOLE GAME.  A signature is over bytes.  If the verifier
rebuilds those bytes even slightly differently from the signer, every honest
attestation fails and you learn nothing.  Two rules keep it stable, and both
are easy to get wrong:

  1. Timestamps are carried as STRINGS and used VERBATIM.  Never parse a
     timestamp and re-format it before verifying.  The signer writes RFC3339
     with nanosecond precision and trailing zeros trimmed; most languages'
     datetime types cannot hold nanoseconds, so a parse-and-reformat round trip
     silently truncates and the signature dies.  Carry the string.
  2. The JSON is compact (no spaces), fields are in declaration order (not
     alphabetical), text is raw UTF-8, and `<`, `>`, `&` are \\u-escaped —
     because the production signer is Go's encoding/json, and that is what it
     emits.  Interop with a real system means matching the real system.

The vectors in ../vectors/ were produced by the production Go signer
(ops/time-hygiene/internal/attest in goatcore).  If this file drifts
from it, tests/verify_vectors fails.
"""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any

ALG = "ntp-attest-v1"

#: The exact, ordered field set the signature covers.  Order is load-bearing:
#: Go's encoding/json emits struct fields in declaration order, not sorted.
SIGNING_VIEW_FIELDS = (
    "alg",
    "host_id",
    "ntp_class_str",
    "selected_source",
    "stratum",
    "ref_id",
    "rms_offset_ns",
    "last_updated_utc",
    "valid_until",
)


class Unverifiable(Exception):
    """The attestation cannot be checked — malformed, or an alg we do not know.

    Distinct from "the signature did not match".  A reader that conflates the
    two either rejects future-versioned attestations it should merely ignore,
    or accepts garbage.
    """


def signing_view(verdict: dict[str, Any]) -> dict[str, Any]:
    """The subset of `verdict` the signature covers, in signing order.

    Timestamps are copied through as the strings they arrived as — see rule 1
    in the module docstring.
    """
    return {
        "alg": ALG,
        "host_id": verdict.get("host_id", ""),
        "ntp_class_str": verdict.get("ntp_class_str", ""),
        "selected_source": verdict.get("selected_source", ""),
        "stratum": verdict.get("stratum", 0),
        "ref_id": verdict.get("ref_id", ""),
        "rms_offset_ns": verdict.get("rms_offset_ns", 0),
        "last_updated_utc": verdict.get("last_updated_utc", ""),
        "valid_until": verdict.get("valid_until", ""),
    }


def signing_bytes(verdict: dict[str, Any]) -> bytes:
    """The deterministic byte form fed to Ed25519.

    Compact separators, declaration order, raw UTF-8, Go-style HTML escaping.
    Signer and verifier both route through this one function so they cannot
    diverge — the same discipline the production Go code uses.
    """
    text = json.dumps(
        signing_view(verdict), separators=(",", ":"), ensure_ascii=False, sort_keys=False
    )
    # Go's encoding/json escapes these three by default (SetEscapeHTML(true)).
    text = text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return text.encode("utf-8")


def verify(verdict: dict[str, Any]) -> bool:
    """Does this verdict carry a signature valid over its own embedded key?

    Returns False for an honestly-unattested verdict (`attested: false`) — that
    is a legitimate posture, not an error.  Raises Unverifiable for a malformed
    or unknown-alg attestation.

    THIS DOES NOT ESTABLISH TRUST IN THE KEY.  It proves internal consistency:
    whoever holds that key made this claim.  Trust in the key itself is rooted
    elsewhere — the host's public attestation key is carried in its
    offline-CA-signed enrollment bundle, so key authenticity chains to a CA
    whose private half lives on no network-reachable host.  A verifier that
    stops here has proven a self-signed statement and nothing more.
    """
    if not verdict.get("attested"):
        return False
    alg = verdict.get("attestation_alg", "")
    if alg != ALG:
        raise Unverifiable(f"unrecognised attestation alg {alg!r}")
    try:
        pub = base64.b64decode(verdict["attestation_pubkey"], validate=True)
        sig = base64.b64decode(verdict["signature"], validate=True)
    except (KeyError, ValueError) as exc:
        raise Unverifiable(f"malformed attestation encoding: {exc}") from exc
    if len(pub) != 32:
        raise Unverifiable(f"pubkey length {len(pub)}, want 32")
    if len(sig) != 64:
        raise Unverifiable(f"signature length {len(sig)}, want 64")
    return _ed25519_verify(pub, signing_bytes(verdict), sig)


def expired(verdict: dict[str, Any], now: datetime | None = None) -> bool:
    """Has the signed validity window closed?

    Staleness is a SEPARATE failure mode from forgery, and it is the one that
    actually bites: a perfectly valid signature over a verdict from four hours
    ago tells you what the clock was doing four hours ago.  A consumer must
    check both.  `valid_until` is inside the signed view, so the window cannot
    be stretched by whoever relays the message.
    """
    now = now or datetime.now(timezone.utc)
    raw = verdict.get("valid_until", "")
    if not raw:
        return True
    return now > _parse_rfc3339(raw)


def _parse_rfc3339(s: str) -> datetime:
    """Parse for COMPARISON ONLY — never feed the result back into signing.

    Python's datetime holds microseconds; the wire carries nanoseconds.  That
    loss is harmless when you are asking "is this older than five minutes" and
    fatal when you are rebuilding signed bytes.
    """
    s = s.replace("Z", "+00:00")
    if "." in s:
        head, rest = s.split(".", 1)
        frac, tz = (rest.split("+", 1) + [""])[:2]
        frac = frac.rstrip("0")[:6].ljust(6, "0")
        s = f"{head}.{frac}+{tz}" if tz else f"{head}.{frac}"
    return datetime.fromisoformat(s)


# --- Ed25519 backend -------------------------------------------------------
# `cryptography` when present (fast, audited); a bundled pure-Python RFC 8032
# reference otherwise, so a bare clone with no pip install still runs the whole
# repo.  Both are exercised against the same production vectors in
# tests/verify_vectors.py, so "which backend" never changes a verdict.

def _ed25519_verify(pub: bytes, msg: bytes, sig: bytes) -> bool:
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric import ed25519 as _c
    except ImportError:
        from . import ed25519_ref

        return ed25519_ref.verify(pub, msg, sig)
    try:
        _c.Ed25519PublicKey.from_public_bytes(pub).verify(sig, msg)
        return True
    except InvalidSignature:
        return False


def backend_name() -> str:
    try:
        import cryptography  # noqa: F401
    except ImportError:
        return "pure-python RFC 8032 reference (lib/ed25519_ref.py)"
    return "cryptography (libcrypto Ed25519)"
