# 4 — The attested liar

**Run:** `python3 run.py` (or `bin/hello-time 4`) · **Needs:** nothing

> **Model, not product.** The mutual-synchronisation engine this exercises is
> designed and not built. Nothing here touches a goatnet.

Ten participants: nine honest, one enrolled and attested and reporting a clock
five seconds from where it really is. Same fleet, same seed, three averaging
rules.

Under a plain mean, one liar takes the ensemble roughly three seconds off UTC
and leaves the honest nodes a second apart from each other. Under a trimmed
mean, it gets nowhere.

This is why the design departs from the gossip-synchronisation research it is
based on: a plain mean is the accuracy-optimal estimator when everyone is
honest, and that research explicitly does not model an adversary. On a fabric
whose threat model includes a captured node, the same choice is a single-node
capture of fabric time.

It also shows the limit of attestation. The signature proved *who* was speaking.
It had nothing to say about whether the content was true.

The tolerable fraction of colluding liars is an **open item**, not a settled
number. This scenario shows the shape of the difference and does not prove a
bound.
