#!/usr/bin/env bash
# Scenario 6 — why a box with no battery-backed clock cannot rejoin its own mesh.
#
# Fully local. Needs only openssl. Nothing is deployed, nothing is contacted.
set -uo pipefail

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  B=$'\033[1m'; D=$'\033[2m'; G=$'\033[32m'; RD=$'\033[31m'; Z=$'\033[0m'
else
  B=""; D=""; G=""; RD=""; Z=""
fi
bold() { printf '%s%s%s\n' "$B" "$1" "$Z"; }
dim()  { printf '%s%s%s\n' "$D" "$1" "$Z"; }
green(){ printf '%s%s%s\n' "$G" "$1" "$Z"; }
red()  { printf '%s%s%s\n' "$RD" "$1" "$Z"; }
step() { printf '\n%s%s.%s %s\n\n' "$B" "$1" "$Z" "$2"; }

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl not found — this scenario needs it. Everything else in the repo does not."
  exit 0
fi

# Portable "N days from now" in the UTCTime form openssl wants (YYMMDDHHMMSSZ).
utc_offset_days() {
  date -u -v"$1"d +%y%m%d%H%M%SZ 2>/dev/null \
    || date -u -d "$1 days" +%y%m%d%H%M%SZ 2>/dev/null
}

printf '\n'; bold "Scenario 6 — the 1970 problem"
dim "─────────────────────────────"

step 1 "Mint a node certificate, the way enrollment does."
openssl req -new -newkey ec -pkeyopt ec_paramgen_curve:P-256 \
  -keyout "$WORK/key.pem" -out "$WORK/req.csr" -nodes -subj "/CN=edge-node-17" 2>/dev/null

NB=$(utc_offset_days -10); NA=$(utc_offset_days +20)
BACKDATED=1
if ! openssl x509 -req -in "$WORK/req.csr" -signkey "$WORK/key.pem" \
      -not_before "$NB" -not_after "$NA" -out "$WORK/cert.pem" 2>/dev/null; then
  # Older openssl without -not_before: issue from now, and say so.
  BACKDATED=0
  openssl req -x509 -key "$WORK/key.pem" -out "$WORK/cert.pem" -days 30 \
    -subj "/CN=edge-node-17" 2>/dev/null
fi
echo "   subject    CN=edge-node-17"
echo "   notBefore  $(openssl x509 -in "$WORK/cert.pem" -noout -startdate | cut -d= -f2)"
echo "   notAfter   $(openssl x509 -in "$WORK/cert.pem" -noout -enddate | cut -d= -f2)"
dim "   A validity window is a claim about UTC. Nothing else in the fabric's"
dim "   security depends on the wall clock this directly."

step 2 "The node is running and its clock is right."
if openssl verify -CAfile "$WORK/cert.pem" "$WORK/cert.pem" >/dev/null 2>&1; then
  green "   verify at the current clock: OK"
else
  red "   verify at the current clock: FAILED (unexpected)"
fi

step 3 "Now cold-boot it with no battery-backed clock and no network."
dim "   An RTC-less board — the Jetson AGX Orin is the one that bit us — comes"
dim "   up at the epoch. It has no way to know better: the clock hardware does"
dim "   not remember, and the network that would tell it is cut."
printf '\n'
openssl verify -attime 3600 -CAfile "$WORK/cert.pem" "$WORK/cert.pem" 2>&1 \
  | sed "s|$WORK/||" | sed 's/^/   /'
printf '\n'
red "   Every mTLS handshake this node attempts now fails the same way."
dim "   Not the fabric, not the mesh, not the identity provider, not the"
dim "   registry — all of them, because all of them check a validity window."
dim "   The node cannot rejoin its own mesh to be told what time it is. That is"
dim "   a deadlock, and it lands precisely in the denied-edge condition the whole"
dim "   design is built for."

step 4 "The fix is two layers, and they close different halves."
if [ "$BACKDATED" = "1" ]; then
  LAST_GOOD=$(( $(date +%s) - 86400 ))
  if openssl verify -attime "$LAST_GOOD" -CAfile "$WORK/cert.pem" "$WORK/cert.pem" >/dev/null 2>&1; then
    green "   verify at last-known-good, 24 h stale: OK"
  else
    red   "   verify at last-known-good, 24 h stale: FAILED"
  fi
  dim "   A day-stale clock is still inside the window. 1970 is not. That gap is"
  dim "   the entire value of remembering roughly what time it was."
else
  dim "   (This openssl cannot backdate notBefore, so the stale-clock check is"
  dim "    skipped here; the certificate above starts at 'now'.)"
fi
cat <<'MSG'

   fake-hwclock     persists the wall clock to disk hourly and on shutdown, and
                    restores it at boot BEFORE the network comes up, so the node
                    starts a bit stale instead of starting in 1970. It only ever
                    moves the clock FORWARD, so it can never drag a healthy host
                    backwards — which is why it is safe to leave on fleet-wide,
                    including on hardware that has a real RTC. Closes the
                    OFFLINE case.

   chrony-presync   steps the clock to correct as soon as any time source is
                    reachable, and does it BEFORE the container runtime starts,
                    so nothing comes up holding a wrong idea of now. Closes the
                    ONLINE case.

   Neither is sufficient alone, which is why both are on by default rather than
   offered as options.
MSG

step 5 "The ordering trap underneath."
cat <<'MSG'
   Services that start before the clock is stepped can cache a wrong "now",
   write records stamped in the wrong era, or decide a fresh credential has
   already expired. The rule is a boot ordering rule, not a monitoring rule:
   the clock is settled before anything that reads it starts. A dependency
   edge, not an alert.
MSG

printf '\n'
dim "   Done. Back to the README for how this reaches your own service."
