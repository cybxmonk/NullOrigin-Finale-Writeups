# NullOrigin Finale Writeups

## Challenge: Event Horizon (Not an easy horizon)

**Flag:** `Null0rigin{event_horizon_uncomputable_2fa8}`

### Introduction
Event Horizon is an expert-level blackbox cryptography challenge simulating quantum observations around a hidden singularity state.
The application exposes a noisy binary parity oracle over $\mathbb{F}_2^{256}$ with thermal entropy fluctuations instead of true random noise.
By querying 256 quantum basis vectors and performing statistical majority voting, participants can reconstruct the full 256-bit target preimage and collapse the singularity.

---

### Contents
- [`Not an easy horizon/Writeup.md`](./Not%20an%20easy%20horizon/Writeup.md) — Complete technical writeup and mathematical breakdown.
- [`Not an easy horizon/solve.py`](./Not%20an%20easy%20horizon/solve.py) — Automated blackbox parallel solver script.
