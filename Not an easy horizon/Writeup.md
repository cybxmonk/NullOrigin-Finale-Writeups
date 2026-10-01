# Event Horizon — Challenge Writeup

## Overview
**Event Horizon** presents a blackbox web service simulating quantum measurements and spacetime event tracking around a hidden singularity state.

### Public Endpoints
- `GET /` — Interactive web application interface.
- `GET /timeline` — Telemetry reporting the current epoch, entropy source (`thermal_fluctuation`), and event count.
- `POST /observe` — Probe interaction endpoint returning a collapsed binary measurement (`0` or `1`).
- `POST /collapse` — Submits the candidate 256-bit hexadecimal preimage state.

---

## Vulnerability & Mathematical Mechanism

### Original Problem
In the initial implementation, `/observe` returned independent random bits uncorrelated with `TARGET`, making the 256-bit search space ($2^{256}$) mathematically unsolvable.

### Redesigned Architecture (Quantum Basis Projection & Noisy Oracle)
The redesigned backend models a noisy quantum observation channel (Goldreich-Levin / Bernstein-Vazirani with depolarizing thermal noise):

1. **Hidden State**:
   A 256-bit random vector $T \in \mathbb{F}_2^{256}$ generated at initialization.

2. **Probe Evaluation**:
   When a basis vector $v \in \mathbb{F}_2^{256}$ is passed via `probe`, the server computes the inner product parity over $\mathbb{F}_2$:
   $$\text{parity} = \langle T, v \rangle = \left(\sum_{k=0}^{255} T_k v_k\right) \bmod 2$$

3. **Noise Channel**:
   Due to thermal fluctuations, the measured outcome experiences a 15% crossover probability:
   $$\text{observed} = b \oplus \text{parity} \oplus \text{noise}, \quad P(\text{noise} = 0) = 0.85$$

4. **Basis Recovery**:
   Setting standard basis vectors $v_i = 1 \ll i$ directly isolates the $i$-th bit:
   $$\langle T, e_i \rangle = T_i$$

---

## Statistical Solution Methodology

Using a majority vote over $M = 17$ independent samples per basis state:
- For true bit $T_i = 1$, expected ones $\mu = 17 \times 0.85 = 14.45$.
- For true bit $T_i = 0$, expected ones $\mu = 17 \times 0.15 = 2.55$.
- Decision threshold: $\text{ones} > 8$.
- Error probability per bit: $P(\text{error}) < 10^{-4}$.
- Total HTTP requests required: $256 \times 17 = 4,352$.

Reconstructing the 32-byte integer into big-endian hexadecimal produces the exact 256-bit target preimage for `POST /collapse`.

---

## Verification & Output

Running `python solve.py http://127.0.0.1:8000`:
```text
[+] Starting Blackbox Solver against http://127.0.0.1:8000
[*] Timeline status: Epoch=1790282382, Entropy=thermal_fluctuation, Target=redacted
[*] Probing 256 quantum basis states...
    Recovered 64/256 bits...
    Recovered 128/256 bits...
    Recovered 192/256 bits...
    Recovered 256/256 bits...
[+] Target state recovered in 17.59s: 911b71de32cbeb531b39ac0b8220f55cd3486730a5d0e34c0cc2fbaba136fb13
[*] Submitting recovered preimage to /collapse...
[+] SUCCESS! Singularity collapsed.
[+] FLAG: Null0rigin{event_horizon_uncomputable_2fa8}
```
