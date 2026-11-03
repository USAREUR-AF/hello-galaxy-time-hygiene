# 6 — The 1970 problem

**Run:** `./run.sh` (or `bin/hello-time 6`) · **Needs:** `openssl`. Nothing is
deployed and nothing is contacted.

Mints a node certificate, verifies it at the current clock, then verifies it as
a board with no battery-backed clock sees it after a cold boot: at the epoch.
OpenSSL names the failure itself — *certificate is not yet valid or the system
clock is incorrect*.

The consequence is worse than one failed check. Every mTLS handshake fails the
same way: fabric, mesh, identity provider, registry — all of them check a
validity window. So the node cannot rejoin its own mesh to be told what time it
is. That deadlock lands precisely in the denied-edge condition the whole design
exists for.

Two layers close it, and they close different halves:

- **`fake-hwclock`** persists the wall clock to disk and restores it at boot
  before the network, so the node starts *stale* rather than starting in 1970 —
  and stale is inside the window, as the run shows. It only ever moves the clock
  forward, which is why it is safe to leave on fleet-wide.
- **`chrony-presync`** steps the clock as soon as any source is reachable, and
  does it before the container runtime starts.

The last point is a boot **ordering** rule, not a monitoring rule: the clock is
settled before anything that reads it starts. A dependency edge, not an alert.
