#!/usr/bin/env bash
# Scenario 1 — read the time surface and learn to read it correctly.
#
# Needs: the `goat` CLI and a goatnet you can reach. GOAT_CONTEXT selects it;
# unset, the CLI's current context is used. Everything else in this repo runs
# with neither.
set -uo pipefail

CONTEXT="${GOAT_CONTEXT:-}"
GOAT="${GOAT_BIN:-goat}"
CTX_ARGS=()
[ -n "$CONTEXT" ] && CTX_ARGS=(--context "$CONTEXT")

say() { printf '\n\033[1m%s\033[0m\n' "$1"; }
note() { printf '\033[2m   %s\033[0m\n' "$1"; }

say "Scenario 1 — the two watches"

if ! command -v "$GOAT" >/dev/null 2>&1; then
  cat <<'MSG'
   goat CLI not found on PATH.

   This scenario is the only one in the repo that needs a goatnet. The other
   five run offline. Install the CLI (goatcore), or read
   scenarios/01-two-watches/README.md, which carries an annotated example of
   what this prints.
MSG
  exit 0
fi

say "1. What the fabric says about its own clocks"
note "goat ${CTX_ARGS[*]:-} health --domain time"
"$GOAT" ${CTX_ARGS[@]+"${CTX_ARGS[@]}"} health --domain time 2>&1 | grep -v 'Skipping name verification'
rc=${PIPESTATUS[0]}
if [ "$rc" -ne 0 ]; then
  cat <<MSG

   Could not reach the goatnet. That is a network/enrollment matter, not a
   time matter — try 'goat ${CTX_ARGS[*]:-} doctor', which walks the chain.
   The README for this scenario has an annotated example.
MSG
  exit 0
fi

cat <<'MSG'

   HOW TO READ THAT TABLE

   STATE     the 5-state honesty signal: green / amber / red / idle / unmetered.
             idle is not a mild green. It means UNCONFIRMED — either the host
             stopped reporting, or what it reported was not signed. See
             scenario 2.

   VERDICT   the per-host agent's own class, from chrony's tracking data:
             healthy (<=1 ms RMS, stratum <=4) / warning / degraded / unknown.

   OFFSET    chrony's running RMS estimate of that host's own error.

   STR       stratum — distance from a reference clock. 16 means unsynchronised;
             10 or above means orphan mode, which is the sneaky one: the host is
             quoting itself as its own reference and looks fine from inside.

   GNSS      whether a satellite receiver is contributing. A dash is normal and
             not a fault: GNSS is an opportunistic anchor, not a requirement.

   ATTEST    age of the newest SIGNED verdict from that host. 'no' means the
             host is speaking unattested — see scenario 3.

   THE THING THE TABLE IS NOT TELLING YOU YET

   The footer names two watches: internal coherence and UTC confidence. Today
   the colour is driven by the UTC-confidence half only — the per-host chrony
   verdict. Internal coherence has no field on the wire yet, because the engine
   that would measure it (peer mutual synchronisation, ADR 1037) is designed and
   not built. That is stated in the code that publishes this surface, and it is
   the single most important honesty caveat in this repo. Scenarios 4 and 5
   model what that engine would do; they do not run it.
MSG

say "2. The population being measured"
note "A small goatnet's roll-up may see only its management host. One host"
note "cannot disagree with anyone, so peer"
note "consensus (the whole point) has nothing to work with there. The roll-up is"
note "correct and the sample is thin; both things are true. Read the count in"
note "the 'n=' line above rather than assuming a fleet."

say "Done. Next: scenarios/02-absence-is-not-health"
