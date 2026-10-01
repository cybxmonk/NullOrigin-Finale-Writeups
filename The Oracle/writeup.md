# Solution Writeup: The Oracle

## Overview
- **Target**: The Oracle Web Service
- **Category**: Cryptography / Web Exploitation
- **Vulnerability**: Secret-Prefix SHA-512 Hash Length Extension
- **Endpoints**:
  - `GET /` - Web UI
  - `GET /status` - Health check & crypto configuration (`mac`, `key_length`)
  - `POST /oracle` - Signature generation endpoint
  - `POST /verify` - Token verification endpoint

---

## Technical Background
The application protects messages using a naive secret-prefix Message Authentication Code (MAC):
$$\text{MAC}(m) = \text{SHA-512}(\text{SECRET} \parallel m)$$

Because SHA-512 utilizes the Merkle–Damgård construction, it is vulnerable to a **Hash Length Extension Attack**:
- An attacker knowing the hash of an unknown secret prefixed to message $m$ ($H(\text{SECRET} \parallel m)$) and the length of the secret can append additional data $m'$ to the message.
- The attacker can calculate the valid hash $H(\text{SECRET} \parallel m \parallel \text{padding} \parallel m')$ without ever knowing the $\text{SECRET}$.

---

## Steps to Solve

### Step 1: Reconnaissance
1. Query the `/status` endpoint:
   ```bash
   curl -s https://the-oracle.onrender.com/status
   ```
2. Observe the JSON response:
   ```json
   {
     "version": "9.9.9",
     "oracle": "online",
     "entropy": "healthy",
     "mac": "SHA512-Prefix",
     "key_length": 32
   }
   ```
3. Key discoveries:
   - The MAC construction is `SHA512-Prefix`.
   - The server's secret key length is `32` bytes.

---

### Step 2: Querying Base Signature
1. Request a signature for a non-privileged query (e.g. `user=guest`) via `POST /oracle`:
   ```bash
   curl -s -X POST https://the-oracle.onrender.com/oracle \
     -H "Content-Type: application/json" \
     -d '{"question": "user=guest"}'
   ```
2. The server returns:
   ```json
   {
     "question": "user=guest",
     "signature": "<128-hex-character-sha512-digest>",
     "answer": "...",
     "confidence": 0.8,
     "proof": "..."
   }
   ```
3. Note that attempting to directly sign `role=oracle_master` returns an HTTP 403 error:
   ```json
   {"error": "The oracle refuses to speak the sacred title directly."}
   ```

---

### Step 3: Performing the SHA-512 Length Extension Attack
1. Parameters:
   - Secret Length: `32` bytes
   - Original Message: `b"user=guest"` (10 bytes)
   - Original Signature: Hex digest from Step 2
   - Data to Append: `b"&role=oracle_master"`
2. Construct the forged message:
   $$\text{forged\_msg} = \text{orig\_msg} \parallel \text{pad}_1 \parallel \text{append\_data}$$
   Where $\text{pad}_1$ is the SHA-512 padding for a total length of $(32 + 10) = 42$ bytes (1024-bit block size):
   - A single `0x80` byte.
   - Zero-padding bytes.
   - 16 bytes representing the 128-bit big-endian bit length ($42 \times 8 = 336$ bits).
3. Compute the forged signature by restoring the internal state $(H_0 \dots H_7)$ from the 128-character hex digest and processing the appended block.

---

### Step 4: Verification and Flag Extraction
1. Submit the forged payload and signature to `POST /verify`:
   ```bash
   curl -s -X POST https://the-oracle.onrender.com/verify \
     -H "Content-Type: application/json" \
     -d '{
       "message_hex": "<forged_message_hex>",
       "signature": "<forged_signature_hex>"
     }'
   ```
2. Server validates the signature and confirms `b"role=oracle_master"` is present:
   ```json
   {
     "ok": true,
     "flag": "Null0rigin{oracle_impossible_7e91}"
   }
   ```

---

## Automated Exploit Execution
Run the provided [`PoC.py`](./PoC.py) against the target instance:
```bash
python PoC.py --url https://the-oracle.onrender.com
```
