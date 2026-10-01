#!/usr/bin/env python3
"""
FANTASMA — El Punto Final Invisible
Automated Blackbox Exploit & Mathematical State Reconstruction Solver

Author: NullOrigin Endgame Suite
Difficulty: INSANE
Category: Web / Logic / Spectral State Reconstruction
"""

import sys
import argparse
import requests

def mod_inv(a: int, m: int) -> int:
    """Compute modular inverse using Extended Euclidean Algorithm."""
    return pow(a, -1, m)

def matrix_inverse_mod_p(matrix, p):
    """
    Invert an N x N matrix over finite field F_p using Gauss-Jordan elimination.
    Pure Python implementation for standalone portability.
    """
    n = len(matrix)
    # Augment matrix with identity
    aug = [row[:] + [1 if i == j else 0 for j in range(n)] for i, row in enumerate(matrix)]
    
    for col in range(n):
        # Find pivot
        pivot_row = None
        for row in range(col, n):
            if aug[row][col] % p != 0:
                pivot_row = row
                break
        if pivot_row is None:
            raise ValueError(f"Matrix is singular over F_{p}")
            
        # Swap rows
        aug[col], aug[pivot_row] = aug[pivot_row], aug[col]
        
        # Scale pivot row to make diagonal element 1
        inv_pivot = mod_inv(aug[col][col] % p, p)
        aug[col] = [(val * inv_pivot) % p for val in aug[col]]
        
        # Eliminate column entries in other rows
        for row in range(n):
            if row != col and aug[row][col] % p != 0:
                factor = aug[row][col] % p
                aug[row] = [(aug[row][k] - factor * aug[col][k]) % p for k in range(2 * n)]
                
    # Extract inverted matrix
    inv = [row[n:] for row in aug]
    return inv

def matrix_vec_mult_mod_p(matrix, vec, p):
    """Multiply N x N matrix with N-dimensional vector over F_p."""
    n = len(matrix)
    res = [0] * n
    for i in range(n):
        acc = 0
        for j in range(n):
            acc = (acc + matrix[i][j] * vec[j]) % p
        res[i] = acc
    return res

def solve_fantasma(base_url: str):
    base_url = base_url.rstrip('/')
    session = requests.Session()
    
    print("=" * 65)
    print("FANTASMA // EL PUNTO FINAL INVISIBLE // BLACKBOX SOLVER")
    print("=" * 65)
    print(f"[*] Target Endpoint: {base_url}")
    
    # 1. Fetch System Telemetry
    print("\n[Phase 1] Probing System Telemetry & Field Parameters...")
    status_url = f"{base_url}/api/system/status"
    r = session.get(status_url)
    if r.status_code != 200:
        print(f"[-] Failed to reach status endpoint: {r.status_code} {r.text}")
        sys.exit(1)
        
    data = r.json()
    telemetry = data.get("telemetry", {})
    p = telemetry.get("field_modulus", 1000000007)
    dim = telemetry.get("state_dimension", 16)
    harmonics = telemetry.get("spectral_harmonics", [])
    
    print(f"    [+] Field Modulus (p):      {p}")
    print(f"    [+] Dimension (N):          {dim}")
    print(f"    [+] Node Harmonics:         {harmonics}")
    print(f"    [+] Current State Status:   {data.get('state_status')}")

    # 2. Probe Ground-State Idle Offset (beta)
    print("\n[Phase 2] Probing Zero-Vector Idle Calibration (Ground State Offset beta)...")
    observe_url = f"{base_url}/api/observe"
    zero_probe = [0] * dim
    r = session.post(observe_url, json={"probe_vector": zero_probe})
    if r.status_code != 200:
        print(f"[-] Observe probe failed: {r.status_code} {r.text}")
        sys.exit(1)
        
    zero_res = r.json()
    beta = zero_res["spectral_flux"]
    print(f"    [+] Measured Baseline Offset beta = {beta}")

    # 3. Non-linear Cubic Distortion Inversion Exponent
    # Exponent e = 3 in F_p, d = 3^(-1) mod (p - 1)
    d = mod_inv(3, p - 1)
    print(f"    [+] Distortion Inversion Exponent d = 3^(-1) mod (p-1) = {d}")

    # 4. Probing 16 Standard Basis Vectors e_0 ... e_15
    print("\n[Phase 3] Transmitting Basis Probes e_0 ... e_15...")
    Z = []
    for j in range(dim):
        basis_probe = [1 if k == j else 0 for k in range(dim)]
        r = session.post(observe_url, json={"probe_vector": basis_probe})
        if r.status_code != 200:
            print(f"[-] Basis probe e_{j} failed: {r.status_code} {r.text}")
            sys.exit(1)
            
        flux = r.json()["spectral_flux"]
        # Invert non-linear distortion: z_j = ((flux - beta) mod p)^d mod p
        z_j = pow((flux - beta) % p, d, p)
        Z.append(z_j)
        print(f"    [+] Basis e_{j:02d} -> Flux: {flux:<11} -> Unfolded Projector z_{j:02d} = {z_j}")

    # 5. Constructing Vandermonde Spectral Coupling Operator W
    print("\n[Phase 4] Synthesizing Vandermonde Operator W & Inverting Transpose Matrix...")
    W = []
    for i in range(dim):
        row = []
        omega = harmonics[i]
        for j in range(dim):
            row.append(pow(omega, j, p))
        W.append(row)
        
    # Transpose of W
    W_T = [[W[j][i] for j in range(dim)] for i in range(dim)]
    
    # Invert W^T modulo p
    W_T_inv = matrix_inverse_mod_p(W_T, p)
    print("    [+] Transposed Spectral Matrix (W^T)^(-1) inverted successfully over F_p.")

    # 6. Reconstructing Hidden Ground State Vector S
    print("\n[Phase 5] Reconstructing 16-Dimensional Hidden State Vector S = (W^T)^(-1) * Z mod p...")
    S = matrix_vec_mult_mod_p(W_T_inv, Z, p)
    print("    [+] Reconstructed Ground State Vector S:")
    for i in range(0, dim, 4):
        chunk = ", ".join(f"s[{k}]={S[k]}" for k in range(i, min(i+4, dim)))
        print(f"        {chunk}")

    # 7. Executing Wavefunction Collapse on /api/collapse
    print("\n[Phase 6] Submitting State Vector to State Collapse Chamber (El Punto Final Invisible)...")
    collapse_url = f"{base_url}/api/collapse"
    r = session.post(collapse_url, json={"state_vector": S})
    
    if r.status_code == 200:
        collapse_res = r.json()
        print("\n" + "=" * 65)
        print("[+] SUCCESS: WAVEFUNCTION COLLAPSED INTO SINGULARITY!")
        print(f"[+] Message: {collapse_res.get('message')}")
        print(f"[+] Energy:  {collapse_res.get('final_state_energy')}")
        print(f"[+] FLAG:    {collapse_res.get('flag')}")
        print("=" * 65)
        return collapse_res.get('flag')
    else:
        print(f"[-] Collapse failed ({r.status_code}): {r.text}")
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Solver for Fantasma CTF Challenge")
    parser.add_argument("--url", default="http://127.0.0.1:5000", help="Base URL of deployed Fantasma app")
    args = parser.parse_args()
    
    solve_fantasma(args.url)
