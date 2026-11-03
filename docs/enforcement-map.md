# Where time is actually enforced

Time hygiene is only worth measuring if something acts on it. This is the map of
what acts, and where — with build state named, because several rows are designed
rather than deployed.

| plane | enforcement point | reads | action | state |
|---|---|---|---|---|
| management hosts | admit-fail-safe sidecar in front of the management API | the local agent's Unix socket | refuse admit-class calls when the verdict is not healthy; revoke-class calls always allowed | built (`ntp-admit-sidecar`) and wired into the generic site stand-up where a management API is present |
| mesh enrollment | setup-key activation pre-hook | the enrolling peer's attestation block, plus a round-trip-time sanity check | deny enrollment on a missing, malformed or implausible attestation | designed |
| role governance | demote job | Prometheus, sustained degradation over minutes | move a peer from the publisher group to the subscriber group | designed |
| data fabric, producer side | router interceptor at publish ingress | the local agent, or a remote agent's health endpoint | drop or tag samples from unhealthy producers | designed |
| data fabric, per message | inline `time_quality` envelope | the producer's agent at publish time | consumers weight or discard by source rung and uncertainty | designed (ADR 0514) |
| viewing plane | the site roll-up and `goat health --domain time` | signed per-host attestations on the bus | none — it reveals, it does not gate | **built** |

Note the shape of that table: the surface people look at is built, and most
of the surfaces that would *act* on it are not. That ordering is deliberate —
reveal before enforce, so a gate is never switched on over a signal nobody has
learned to read — and it is also the honest current position rather than a
finished picture.

## Fail closed, on the right axis

Every enforcement point fails **closed**: if the check cannot be performed —
agent unreachable, socket error, malformed response — that is a rejection, not a
pass. An unreachable time-health agent is indistinguishable from a host hiding a
bad clock, and it must be treated as the worse of the two.

With the two-axis model, "fail closed" is asked separately on each axis:

- gate **fabric participation** on internal coherence
- gate **UTC-bound operations** (certificates, tokens, setup keys) on UTC confidence

A node that is coherent but does not know UTC keeps publishing and stops being
trusted to judge a validity window. Under a single verdict, that same node gets
cut off from the fabric entirely — at the denied edge, which is when it is most
needed.

## Publisher and subscriber

The precondition applies to entities that **publish**. Pure subscribers can
participate without it, because they do not influence anyone else's state.

The trap is that "pure subscriber" is much rarer than it sounds. Most
participants publish through at least one channel — a last-seen update, an audit
event, a certificate-expiry assertion, a sensor reading. Pure subscribers are
declared explicitly, never assumed from what a service looks like it does.
