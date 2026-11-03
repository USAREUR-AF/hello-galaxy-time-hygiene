"""Pure-Python Ed25519 verify + sign (RFC 8032), so a bare clone needs no pip.

This is the textbook reference construction: readable, correct, and slow (a few
milliseconds per operation).  It exists so nothing in this repo is gated behind
`pip install`, and so the signature check is something you can read rather than
something you take on faith.  Where `cryptography` is installed, lib/attest.py
uses it instead; tests/verify_vectors.py runs BOTH against the same
production-signed vectors, so the backend never changes an answer.

Not constant-time.  Fine for verifying a public attestation; do not lift this
into anything holding a long-lived secret.
"""

from __future__ import annotations

import hashlib

P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, P - 2, P) % P
I = pow(2, (P - 1) // 4, P)  # noqa: E741 — RFC 8032 names it I


def _h(m: bytes) -> bytes:
    return hashlib.sha512(m).digest()


def _x_recover(y: int) -> int:
    xx = (y * y - 1) * pow(D * y * y + 1, P - 2, P)
    x = pow(xx, (P + 3) // 8, P)
    if (x * x - xx) % P != 0:
        x = (x * I) % P
    if x % 2 != 0:
        x = P - x
    return x


BY = 4 * pow(5, P - 2, P) % P
BX = _x_recover(BY)
B = (BX % P, BY % P, 1, BX * BY % P)


def _add(pt: tuple, q: tuple) -> tuple:
    x1, y1, z1, t1 = pt
    x2, y2, z2, t2 = q
    a = (y1 - x1) * (y2 - x2) % P
    b = (y1 + x1) * (y2 + x2) % P
    c = t1 * 2 * D * t2 % P
    dd = z1 * 2 * z2 % P
    e, f, g, h = b - a, dd - c, dd + c, b + a
    return (e * f % P, g * h % P, f * g % P, e * h % P)


def _mul(pt: tuple, e: int) -> tuple:
    q = (0, 1, 1, 0)
    while e > 0:
        if e & 1:
            q = _add(q, pt)
        pt = _add(pt, pt)
        e >>= 1
    return q


def _encode_point(pt: tuple) -> bytes:
    x, y, z, _ = pt
    zi = pow(z, P - 2, P)
    x, y = x * zi % P, y * zi % P
    return ((y & ~(1 << 255)) | ((x & 1) << 255)).to_bytes(32, "little")


def _decode_point(s: bytes) -> tuple | None:
    y = int.from_bytes(s, "little") & ~(1 << 255)
    x = _x_recover(y)
    if x & 1 != (s[31] >> 7) & 1:
        x = P - x
    pt = (x, y, 1, x * y % P)
    # on-curve check: reject a crafted "public key" that is not a real point
    x, y, z, t = pt
    if (-x * x + y * y - z * z - D * t * t) % P != 0:
        return None
    return pt


def verify(pub: bytes, msg: bytes, sig: bytes) -> bool:
    if len(sig) != 64 or len(pub) != 32:
        return False
    a = _decode_point(pub)
    r = _decode_point(sig[:32])
    if a is None or r is None:
        return False
    s = int.from_bytes(sig[32:], "little")
    if s >= L:  # non-canonical S — malleable, reject
        return False
    k = int.from_bytes(_h(sig[:32] + pub + msg), "little") % L
    return _encode_point(_mul(B, s)) == _encode_point(_add(r, _mul(a, k)))


def sign(seed: bytes, msg: bytes) -> tuple[bytes, bytes]:
    """Returns (signature, public_key). `seed` is the 32-byte private seed."""
    h = _h(seed)
    a = (int.from_bytes(h[:32], "little") & ((1 << 254) - 8)) | (1 << 254)
    pub = _encode_point(_mul(B, a))
    r = int.from_bytes(_h(h[32:] + msg), "little") % L
    rr = _encode_point(_mul(B, r))
    k = int.from_bytes(_h(rr + pub + msg), "little") % L
    return rr + ((r + k * a) % L).to_bytes(32, "little"), pub
