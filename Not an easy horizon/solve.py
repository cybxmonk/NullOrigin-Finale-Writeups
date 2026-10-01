import sys
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = sys.argv[1].rstrip('/') if len(sys.argv) > 1 else 'http://127.0.0.1:8000'

def log(msg):
    print(msg, flush=True)

def check_timeline(session):
    resp = session.get(f"{BASE_URL}/timeline", timeout=15)
    resp.raise_for_status()
    data = resp.json()
    log(f"[*] Timeline status: Epoch={data.get('epoch')}, Entropy={data.get('entropy_source')}, Target={data.get('target')}")

def query_bit(bit_index, samples=15):
    s = requests.Session()
    probe_val = 1 << bit_index
    ones = 0
    valid_samples = 0
    for _ in range(samples):
        try:
            r = s.post(
                f"{BASE_URL}/observe",
                json={"bit": 0, "probe": probe_val},
                timeout=10
            )
            if r.status_code == 200:
                valid_samples += 1
                if r.json().get("observed") == 1:
                    ones += 1
        except Exception:
            time.sleep(0.05)
            continue
    s.close()
    if valid_samples == 0:
        return bit_index, 0
    return bit_index, (1 if ones > (valid_samples / 2) else 0)

def solve():
    log(f"[+] Starting Blackbox Solver against {BASE_URL}")
    main_session = requests.Session()
    
    # 1. Reconnaissance
    check_timeline(main_session)
    
    # 2. Recover 256 bits of the hidden target state in parallel
    log("[*] Probing 256 quantum basis states...")
    start_time = time.time()
    
    bits = [0] * 256
    completed_count = 0
    
    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(query_bit, i, 15) for i in range(256)]
        for fut in as_completed(futures):
            idx, bit_val = fut.result()
            bits[idx] = bit_val
            completed_count += 1
            if completed_count % 32 == 0 or completed_count == 256:
                log(f"    Recovered {completed_count}/256 bits...")

    # 3. Reconstruct 256-bit target integer and hex string
    target_int = 0
    for i, b in enumerate(bits):
        if b:
            target_int |= (1 << i)
            
    target_bytes = target_int.to_bytes(32, "big")
    target_hex = target_bytes.hex()
    
    elapsed = time.time() - start_time
    log(f"[+] Target state recovered in {elapsed:.2f}s: {target_hex}")
    
    # 4. Collapse the singularity
    log("[*] Submitting recovered preimage to /collapse...")
    collapse_resp = main_session.post(
        f"{BASE_URL}/collapse",
        json={"state": target_hex},
        timeout=15
    )
    
    if collapse_resp.status_code == 200:
        res_data = collapse_resp.json()
        if res_data.get("collapsed"):
            log(f"[+] SUCCESS! Singularity collapsed.")
            log(f"[+] FLAG: {res_data.get('flag')}")
            return True
        else:
            log("[-] Collapse failed: returned collapsed=False")
            return False
    else:
        log(f"[-] Collapse rejected with status {collapse_resp.status_code}: {collapse_resp.text}")
        return False

if __name__ == "__main__":
    success = solve()
    if not success:
        sys.exit(1)
