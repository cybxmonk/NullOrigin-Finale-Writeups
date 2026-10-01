#!/usr/bin/env python3
"""
PoC / Exploit Script for The Oracle Challenge.
Demonstrates the Secret-Prefix SHA-512 Hash Length Extension Attack.
"""

import sys
import json
import struct
import argparse
import urllib.request
import urllib.error

# SHA-512 Constants
K512 = [
    0x428a2f98d728ae22, 0x7137449123ef65cd, 0xb5c0fbcfec4d3b2f, 0xe9b5dba58189dbbc,
    0x3956c25bf348b538, 0x59f111f1b605d019, 0x923f82a4af194f9b, 0xab1c5ed5da6d8118,
    0xd807aa98a3030242, 0x12835b0145706fbe, 0x243185be4ee4b28c, 0x550c7dc3d5ffb4e2,
    0x72be5d74f27b896f, 0x80deb1fe3b1696b1, 0x9bdc06a725c71235, 0xc19bf174cf692694,
    0xe49b69c19ef14ad2, 0xefbe4786384f25e3, 0x0fc19dc68b8cd5b5, 0x240ca1cc77ac9c65,
    0x2de92c6f592b0275, 0x4a7484aa6ea6e483, 0x5cb0a9dcbd41fbd4, 0x76f988da831153b5,
    0x983e5152ee66dfab, 0xa831c66d2db43210, 0xb00327c898fb213f, 0xbf597fc7beef0ee4,
    0xc6e00bf33da88fc2, 0xd5a79147930aa725, 0x06ca6351e003826f, 0x142929670a0e6e70,
    0x27b70a8546d22ffc, 0x2e1b21385c26c926, 0x4d2c6dfc5ac42aed, 0x53380d139d95b3df,
    0x650a73548baf63de, 0x766a0abb3c77b2a8, 0x81c2c92e47edaee6, 0x92722c851482353b,
    0xa2bfe8a14cf10364, 0xa81a664bbc423001, 0xc24b8b70d0f89791, 0xc76c51a30654be30,
    0xd192e819d6ef5218, 0xd69906245565a910, 0xf40e35855771202a, 0x106aa07032bbd1b8,
    0x19a4c116b8d2d0c8, 0x1e376c085141ab53, 0x2748774cdf8eeb99, 0x34b0bcb5e19b48a8,
    0x391c0cb3c5c95a63, 0x4ed8aa4ae3418acb, 0x5b9cca4f7763e373, 0x682e6ff3d6b2b8a3,
    0x748f82ee5defb2fc, 0x78a5636f43172f60, 0x84c87814a1f0ab72, 0x8cc702081a6439ec,
    0x90befffa23631e28, 0xa4506cebde82bde9, 0xbef9a3f7b2c67915, 0xc67178f2e372532b,
    0xca273eceea26619c, 0xd186b8c721c0c207, 0xeada7dd6cde0eb1e, 0xf57d4f7fee6ed178,
    0x06f067aa72176fba, 0x0a637dc5a2c898a6, 0x113f9804bef90dae, 0x1b710b35131c471b,
    0x28db77f523047d84, 0x32caab7b40c72493, 0x3c9ebe0a15c9bebc, 0x431d67c49c100d4c,
    0x4cc5d4becb3e42b6, 0x597f299cfc657e2a, 0x5fcb6fab3ad6faec, 0x6c44198c4a475817
]
MASK64 = 0xFFFFFFFFFFFFFFFF


def rotr(x, n):
    return ((x >> n) | (x << (64 - n))) & MASK64


def sha512_compress(state, block):
    w = list(struct.unpack('>16Q', block)) + [0] * 64
    for i in range(16, 80):
        s0 = rotr(w[i - 15], 1) ^ rotr(w[i - 15], 8) ^ (w[i - 15] >> 7)
        s1 = rotr(w[i - 2], 19) ^ rotr(w[i - 2], 61) ^ (w[i - 2] >> 6)
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) & MASK64

    a, b, c, d, e, f, g, h = state
    for i in range(80):
        s1 = rotr(e, 14) ^ rotr(e, 18) ^ rotr(e, 41)
        ch = (e & f) ^ ((~e) & g)
        t1 = (h + s1 + ch + K512[i] + w[i]) & MASK64
        s0 = rotr(a, 28) ^ rotr(a, 34) ^ rotr(a, 39)
        maj = (a & b) ^ (a & c) ^ (b & c)
        t2 = (s0 + maj) & MASK64

        h = g
        g = f
        f = e
        e = (d + t1) & MASK64
        d = c
        c = b
        b = a
        a = (t1 + t2) & MASK64

    return [
        (state[0] + a) & MASK64,
        (state[1] + b) & MASK64,
        (state[2] + c) & MASK64,
        (state[3] + d) & MASK64,
        (state[4] + e) & MASK64,
        (state[5] + f) & MASK64,
        (state[6] + g) & MASK64,
        (state[7] + h) & MASK64,
    ]


def sha512_length_extension(orig_hash_hex: str, orig_data: bytes, secret_len: int, append_data: bytes):
    """
    Computes H(SECRET || orig_data || pad1 || append_data)
    without knowing SECRET.
    """
    state = list(struct.unpack('>8Q', bytes.fromhex(orig_hash_hex)))

    # Original padding: [orig_data] + 0x80 + zeros + 128-bit bit length
    orig_total_len = secret_len + len(orig_data)
    pad1 = b'\x80' + b'\x00' * ((112 - (orig_total_len + 1)) % 128)
    pad1 += struct.pack('>QQ', 0, orig_total_len * 8)

    # Forged message sent to server
    forged_message = orig_data + pad1 + append_data

    # Total length of extended message in bits
    total_extended_len = secret_len + len(forged_message)

    # Padding for the newly appended block
    pad2 = b'\x80' + b'\x00' * ((112 - (total_extended_len + 1)) % 128)
    pad2 += struct.pack('>QQ', 0, total_extended_len * 8)
    stream = append_data + pad2

    for i in range(0, len(stream), 128):
        state = sha512_compress(state, stream[i:i + 128])

    forged_hash = ''.join(f'{x:016x}' for x in state)
    return forged_message, forged_hash


def send_request(url: str, method: str = "GET", data: dict = None):
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None

    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            res_body = response.read().decode("utf-8")
            try:
                return status_code, json.loads(res_body)
            except json.JSONDecodeError:
                return status_code, res_body
    except urllib.error.HTTPError as e:
        status_code = e.code
        err_body = e.read().decode("utf-8")
        try:
            return status_code, json.loads(err_body)
        except json.JSONDecodeError:
            return status_code, err_body
    except urllib.error.URLError as e:
        print(f"[-] Connection failed: {e.reason}")
        return None, None


def main():
    parser = argparse.ArgumentParser(description="The Oracle SHA-512 Length Extension Exploit")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of The Oracle service (default: http://localhost:8000)",
    )
    args = parser.parse_args()
    base_url = args.url.rstrip("/")

    print("=" * 65)
    print(" [*] THE ORACLE // SHA-512 LENGTH EXTENSION EXPLOIT")
    print("=" * 65)

    # Step 1: Query /status
    print("\n[Step 1] Querying /status for parameters...")
    code, status_data = send_request(f"{base_url}/status")
    if code != 200:
        print(f"[-] Failed to reach /status: HTTP {code}")
        sys.exit(1)

    secret_len = status_data.get("key_length", 32)
    mac_type = status_data.get("mac", "SHA512-Prefix")
    print(f"[+] Service online: {status_data.get('oracle')} (v{status_data.get('version')})")
    print(f"[+] Detected MAC: {mac_type} (Key length: {secret_len} bytes)")

    # Step 2: Query /oracle for a base signature
    orig_msg = b"user=guest"
    print(f"\n[Step 2] Querying /oracle for signature over: '{orig_msg.decode()}'...")
    code, oracle_data = send_request(f"{base_url}/oracle", method="POST", data={"question": orig_msg.decode()})
    if code != 200:
        print(f"[-] /oracle failed: HTTP {code} -> {oracle_data}")
        sys.exit(1)

    orig_sig = oracle_data.get("signature")
    print(f"[+] Received signature: {orig_sig[:32]}...{orig_sig[-16:]}")

    # Step 3: Perform Hash Length Extension Attack
    append_data = b"&role=oracle_master"
    print(f"\n[Step 3] Performing SHA-512 Length Extension appending '{append_data.decode()}'...")
    forged_msg, forged_sig = sha512_length_extension(orig_sig, orig_msg, secret_len, append_data)
    print(f"[+] Forged Signature: {forged_sig}")
    print(f"[+] Forged Message (hex): {forged_msg.hex()}")

    # Step 4: Verify forged signature against /verify
    print("\n[Step 4] Submitting forged payload to /verify...")
    code, verify_data = send_request(
        f"{base_url}/verify",
        method="POST",
        data={"message_hex": forged_msg.hex(), "signature": forged_sig}
    )

    if code == 200 and verify_data.get("ok"):
        print("\n" + "*" * 65)
        print(" [+] EXPLOIT SUCCESSFUL! MASTER ACCESS GRANTED!")
        print(f" FLAG: {verify_data.get('flag')}")
        print("*" * 65)
    else:
        print(f"[-] Verification failed (HTTP {code}): {verify_data}")


if __name__ == "__main__":
    main()
