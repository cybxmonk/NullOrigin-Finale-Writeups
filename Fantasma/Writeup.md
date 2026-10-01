# FANTASMA — El Punto Final Invisible
## Official Blackbox CTF Writeup

**Challenge Name:** Fantasma — El Punto Final Invisible  
**Category:** Web / Logic / Spectral State Reconstruction  
**Difficulty:** INSANE  
**Flag:** `NullOrigin{f4nt4sm4_3l_punt0_f1n4l_1nv1s1bl3_qu4ntum_st4t3_r3c0v3r3d}`  

---

## 1. Challenge Overview

**Fantasma** (*El Punto Final Invisible*) presents a dark, futuristic monitoring console for a mysterious quantum spectral observation engine. The system operates over an indeterminate internal ground state $\vec{S} \in \mathbb{F}_p^{16}$ generated randomly on each session. 

The console displays high-level telemetry and allows users to transmit $16$-dimensional probe vectors $\vec{V}$ into the observation engine via `/api/observe`, returning a scalar measurement termed **Spectral Flux** ($y$).

The ultimate goal is to reconstruct the exact 16-dimensional hidden state vector $\vec{S}$ and submit it to the **State Collapse Chamber** (`/api/collapse`) to induce wavefunction collapse and obtain the flag.

---

## 2. Initial Reconnaissance & Blackbox Exploration

Upon loading the application in a web browser, the player discovers the following endpoints:

| Endpoint | Method | Purpose |
| :--- | :---: | :--- |
| `/` | `GET` | Main futuristic web dashboard UI |
| `/api/system/status` | `GET` | Node telemetry, dimension $N=16$, field modulus $p=1000000007$, harmonic roots $\vec{\omega}$ |
| `/api/timeline` | `GET` | Recent system events, including boot trace and ground-state idle calibration |
| `/api/observe` | `POST` | Observation terminal accepting probe vector $\vec{V} = [v_0, \dots, v_{15}]$ |
| `/api/collapse` | `POST` | Final state collapse chamber accepting candidate state vector $\vec{S}$ |
| `/api/reset` | `POST` | Resets current session state |

### Key Observations from Public Telemetry

Querying `/api/system/status` returns:
```json
{
  "system": "FANTASMA",
  "subtitle": "El Punto Final Invisible",
  "node_id": "PH-07",
  "status": "ONLINE",
  "observation_engine": "ACTIVE",
  "state_status": "SUPERPOSED_INDETERMINATE",
  "telemetry": {
    "field_modulus": 1000000007,
    "state_dimension": 16,
    "spectral_harmonics": [3, 7, 11, 19, 23, 31, 43, 47, 59, 67, 71, 79, 83, 89, 97, 101],
    "probes_executed": 1
  }
}
```

---

## 3. Reverse-Engineering the Mathematical Operator

### Step 1: Identifying the Baseline Offset ($\beta$)

Transmitting the zero probe $\vec{V} = [0, 0, \dots, 0]$ to `/api/observe` (or inspecting the `IDLE_CALIBRATION` entry in `/api/timeline`) consistently yields:
$$\text{Spectral Flux: } y_0 = 4294967$$

Since $\vec{V} = \vec{0}$, any linear projection $\langle \vec{S}, W \vec{V} \rangle = 0$. Thus, $4294967$ represents the ground-state constant offset $\beta$:
$$\beta = 4294967$$

### Step 2: Probing Non-Linear Scaling (The Cubic Permutation)

Testing scalar multiples of the first basis vector $k \cdot \vec{e}_0$ for $k = 1, 2, 3$:
- For $k=1$: $y_1 - \beta = \Delta$
- For $k=2$: $y_2 - \beta \equiv 8 \cdot \Delta \equiv 2^3 \cdot \Delta \pmod p$
- For $k=3$: $y_3 - \beta \equiv 27 \cdot \Delta \equiv 3^3 \cdot \Delta \pmod p$

This proves the observation operator distorts the intermediate projection $z$ via a pure cubic mapping:
$$y = (z^3 + \beta) \pmod p$$

Because $p = 1000000007$ satisfies $\gcd(3, p - 1) = \gcd(3, 1000000006) = 1$, the cubic map $z \mapsto z^3 \pmod p$ is a **bijective permutation polynomial** over $\mathbb{F}_p$.

The unique inverse exponent $d$ is:
$$d = 3^{-1} \pmod{p - 1} = 666666671$$

Thus, given any observed flux $y$, the linear projection $z$ is inverted by:
$$z = (y - \beta)^d \pmod p$$

---

## 4. Reconstructing the Ground State Vector $\vec{S}$

### Step 3: Spectral Mixing Operator Matrix $W$

The system status provides the harmonic frequencies:
$$\vec{\omega} = [3, 7, 11, 19, 23, 31, 43, 47, 59, 67, 71, 79, 83, 89, 97, 101]$$

The underlying spectral coupling operator is a $16 \times 16$ Vandermonde matrix $W$ over $\mathbb{F}_p$:
$$W_{i, j} = \omega_i^j \pmod p \quad (0 \le i, j < 16)$$

When probing with standard basis vector $\vec{e}_j = [0, \dots, 1, \dots, 0]^T$:
$$W \vec{e}_j = \text{column } j \text{ of } W = (\omega_0^j, \omega_1^j, \dots, \omega_{15}^j)^T$$

The inner product projection is:
$$z_j = \langle \vec{S}, W \vec{e}_j \rangle = \sum_{i=0}^{15} s_i \cdot \omega_i^j \pmod p = (W^T \vec{S})_j$$

Collecting all 16 basis measurements forms the vector $\vec{Z} = [z_0, z_1, \dots, z_{15}]^T$:
$$\vec{Z} = W^T \vec{S} \pmod p$$

### Step 4: Matrix Inversion over $\mathbb{F}_p$

Since all roots $\omega_i$ are distinct non-zero elements of $\mathbb{F}_p$, the Vandermonde determinant is non-zero:
$$\det(W) = \prod_{0 \le i < j < 16} (\omega_j - \omega_i) \not\equiv 0 \pmod p$$

Hence, $W^T$ is invertible. Using Gauss-Jordan elimination modulo $p$:
$$\vec{S} = (W^T)^{-1} \vec{Z} \pmod p$$

---

## 5. Wavefunction Collapse & Flag Capture

Submitting the recovered state vector $\vec{S} = [s_0, s_1, \dots, s_{15}]$ to `/api/collapse`:

```http
POST /api/collapse HTTP/1.1
Content-Type: application/json

{
  "state_vector": [s_0, s_1, ..., s_15]
}
```

Response:
```json
{
  "status": "COLLAPSED",
  "message": "Wavefunction collapsed. El Punto Final Invisible reached.",
  "final_state_energy": "0.000 eV (Singularity)",
  "flag": "NullOrigin{f4nt4sm4_3l_punt0_f1n4l_1nv1s1bl3_qu4ntum_st4t3_r3c0v3r3d}"
}
```

---

## 6. Exploit Execution & Verification

The solver `solve.py` executes this full blackbox attack in under $0.5$ seconds using only 18 HTTP requests (1 status probe + 1 zero probe + 16 basis probes + 1 collapse request).
