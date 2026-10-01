# Null Origin Finale — Challenge Writeups

Official solution writeups for the challenges in the Null Origin Finale CTF.

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

* **[Fantasma](Fantasma)** (or [writeup.md](Fantasma/Writeup.md)) — *Hard / Insane*

  * **Theme**: Spectral Harmonic State Reconstruction & Finite Field Polynomial Inversion
  * **Intro**: A quantum spectral monitoring console operating over an indeterminate 16-dimensional ground state vector in GF(p). By inverting a non-linear cubic permutation and solving the Vandermonde spectral coupling matrix, the hidden state vector is reconstructed to collapse the wavefunction.
  * **Flag**: `NullOrigin{f4nt4sm4_3l_punt0_f1n4l_1nv1s1bl3_qu4ntum_st4t3_r3c0v3r3d}`

* **[Señal en capas](Se%C3%B1al%20en%20capas)** (or [writeup.md](Se%C3%B1al%20en%20capas/writeup.md)) — *Easy*

  * **Theme**: Multi-Layered Encoding (Base58 → Base32 → Base45 → ROT13)
  * **Intro**: A multi-layered signal encoding challenge where a concealed message has been consecutively transformed through Base58, Base32, Base45, and ROT13 substitution.
  * **Flag**: `NullOrigin{5y57em_m34ns_3Lv1sh}`
