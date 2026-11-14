# AGENTS.md

Instructions for AI coding agents, and a short version for anyone working here. [CONTRIBUTING.md](CONTRIBUTING.md) is the full process.

## What this repository is

hello-galaxy-time-hygiene is a walkthrough of time on a fabric with no central service: participants keep time by agreeing with each other, external references are optional anchors, and health reports internal agreement and UTC confidence separately. Five of the six scenarios need only Python and `openssl`; scenario 1 reads a live goatnet.

It is one of the Hello Galaxy demonstrations: small, runnable examples, each showing one part of [goat](https://github.com/USAREUR-AF/goatcore). It holds no goat source code.

## Layout

| Path | What |
|---|---|
| `scenarios/` | one directory per scenario |
| `bin/hello-time` | the runner: all, `offline`, one scenario by number, or `test` |
| `lib/` | the reference implementation, including a pure-Python Ed25519 |
| `vectors/` | signed test vectors |
| `tests/verify_vectors.py` | checks the reference against the vectors |

## Before you push

CI (`.github/workflows/ci.yml`) runs these twice, with and without `cryptography` installed; both must pass:

```bash
python3 tests/verify_vectors.py
bin/hello-time offline

pip install -r requirements.txt
python3 tests/verify_vectors.py
bin/hello-time offline
```

## Rules

1. **Nothing from a real deployment.** No hostname, domain, address, key or person of a real goatnet goes into a file or a commit message. Use made-up names, documentation addresses (RFC 5737) and `example.org` mail.
2. **Commits.** Conventional Commits subject of 100 characters or fewer, with a scope (`fix(<component>): …`). Every commit is signed off (`git commit -s`, the DCO) and signed with a key GitHub verifies. The organization's required check `verified-commits` refuses a pull request that holds an unverified commit.
3. **One logical change per pull request.**
4. **Vulnerabilities** go through [SECURITY.md](SECURITY.md), never a public issue.

The contribution guide for goat as a whole is [goatcore CONTRIBUTING.md](https://github.com/USAREUR-AF/goatcore/blob/main/CONTRIBUTING.md).
