# 1 — The two watches

**Run:** `./run.sh` (or `bin/hello-time 1`)
**Needs:** the `goat` CLI and any goatnet you have access to. `GOAT_CONTEXT`
selects which; unset, the CLI's current context is used. This is the **only**
scenario in the repo that needs a goatnet — the other five run offline. The
goatnet can be a one-machine goatlite you stand up
yourself (goatcore's [goatlite quickstart](https://github.com/usareur-af/goatcore/blob/main/docs/tutorials/00-goatlite.md)),
or another goatnet you have access to.

Reads the goatnet's time surface and teaches you to read it correctly: what each
column means, why `idle` is not a mild green, and what the table is not telling
you yet.

## Example output, if you cannot reach a goatnet

Host and site names are illustrative.

```
$ goat --context zagros health --domain time

TIME: GREEN — 1 host clock; all 1 host clock healthy
  site zagros · 30s window · n=1 host

  HOST              STATE   VERDICT       OFFSET  STR  GNSS     ATTEST
  mgmt-zagros-01    GREEN   healthy       0.2 ms    2     —    28s ago

  two watches: internal coherence (ordering/fusion — holds at the denied edge) vs
  UTC confidence (anchor freshness). An unattested host reads idle, never green —
  absence of a signed attestation is never reported as healthy.
```

Three things to notice.

**`n=1 host`.** A small goatnet's roll-up may see one host. One
host cannot disagree with anyone, so the peer-consensus idea has nothing to work
with there. The reading is correct; the sample is thin.

**`GNSS —`.** No satellite receiver is contributing, and the host is green
anyway. That is the design working: an anchor is opportunistic, not a
requirement.

**The footer names two watches; the colour is currently one of them.** It is the
UTC-confidence half, derived from the per-host chrony verdict. Internal coherence
has no field on the wire because the engine that would measure it is not built —
see [../../docs/honesty-matrix.md](../../docs/honesty-matrix.md).
