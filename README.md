# Null Origin Finale — Web Challenge Writeups

Official solution writeups for the Web challenges in the Null Origin Finale CTF.

## Index of Writeups

* **[Not an easy horizon](Not%20an%20easy%20horizon)** (or [writeup.md](Not%20an%20easy%20horizon/Writeup.md)) — *Hard / Insane*

  * **Theme**: Quantum Singularity & Hidden Preimage Recovery
  * **Intro**: Event Horizon simulates quantum measurements around an isolated singularity state. The system exposes a noisy binary parity oracle over GF(2) with thermal fluctuations, allowing full state reconstruction via basis projection.
  * **Flag**: `Null0rigin{event_horizon_uncomputable_2fa8}`

* **[Out Of Context](Out%20Of%20Context)** (or [writeup.md](Out%20Of%20Context/writeup.md)) — *Medium*

  * **Theme**: Authentication-State Confusion & Jinja2 Template Injection (SSTI)
  * **Intro**: An enterprise document template management portal with authentication parameter precedence vulnerability enabling privilege escalation, followed by Jinja2 SSTI sandbox escape via MRO object traversal and filter evasion.
  * **Flag**: `NullOrigin{T3r4_Bh41_S33dh3_m4u7}`

* **[Kuber](Kuber)** (or [writeup.md](Kuber/writeup.md)) — *Medium / Hard*

  * **Theme**: Client-Side Prototype Pollution, DOM XSS & HSM Enclave Bypass
  * **Intro**: A financial vault portal where unvalidated transaction memo parsing leads to client-side prototype pollution, bypassing the HTML sanitizer to achieve DOM XSS, manipulate the same-origin HSM iframe, and decrypt the encrypted vault.
  * **Flag**: `NullOrigin{kUb3rr_15_r1cH_th0ugh}`
