# Writeup — Layered Signal

## Challenge Information

- **Category:** Crypto / Encoding
- **Difficulty:** Easy
- **Flag:** `NullOrigin{5y57em_m34ns_3Lv1sh}`

## Overview

The challenge provides the following encoded string:

```text
n5TTDgmuT1yYA5g4dKUQsFst7uDGxUQoTnZm2SAzZ9t3R8o5vtdFMuYZf9BALRZzEeXkuzbpHHUx7Sv3Br9Ny1qqo7XSomvFy1vGqQLru1y24
```

The string is not encrypted. It has been passed through multiple common encoding and transformation layers. The objective is to identify each layer and reverse the transformations until the flag is recovered.

## Step 1 — Base58

The ciphertext uses characters consistent with the standard Base58 alphabet:

```text
123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
```

It does not contain the commonly excluded characters `0`, `O`, `I`, or `l`.

Decoding the string as Base58 produces:

```text
GRBTQMSHIZLUQOBKF5CUWL2FFVIEMUKVIRFDANZXJRDDQS2GHJJDMSBOIM2U2NSKIRCCULSDLIZA====
```

The resulting string is composed of uppercase letters and Base32 padding, suggesting the next layer is Base32.

## Step 2 — Base32

The decoded value matches the Base32 alphabet and uses `=` padding.

Decoding it as Base32 produces:

```text
4C82GFWH8*/EK/E-PFQUDJ077LF8KF:R6H.C5M6JDD*.CZ2
```

The resulting characters include distinctive Base45 characters such as:

```text
$ % * + - . / :
```

This indicates another encoding layer.

## Step 3 — Base45

The standard Base45 alphabet is:

```text
0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:
```

The intermediate value is valid Base45:

```text
4C82GFWH8*/EK/E-PFQUDJ077LF8KF:R6H.C5M6JDD*.CZ2
```

Decoding it produces:

```text
AhyyBevtva{5l57rz_z34af_3Yi1fu}
```

The text now resembles a flag, but the prefix `AhyyBevtva` is not the expected flag namespace. This suggests a simple substitution such as ROT13.

## Step 4 — ROT13

Applying ROT13:

```text
AhyyBevtva{5l57rz_z34af_3Yi1fu}
```

produces:

```text
NullOrigin{5y57em_m34ns_3Lv1sh}
```

The flag is now recovered.

# Final Flag

```text
NullOrigin{5y57em_m34ns_3Lv1sh}
```

## Complete Transformation Chain

The challenge was constructed using:

```text
FLAG
  ↓
ROT13
  ↓
Base45
  ↓
Base32
  ↓
Base58
  ↓
Ciphertext
```

Therefore, the solver reverses the process:

```text
Ciphertext
  ↓
Base58
  ↓
Base32
  ↓
Base45
  ↓
ROT13
  ↓
FLAG
```

## CyberChef Recipe

Use these operations in CyberChef in this order:

```text
From Base58
From Base32
From Base45
ROT13
```

Paste the challenge ciphertext into the input. The final output is:

```text
NullOrigin{5y57em_m34ns_3Lv1sh}
```

## Skills Learned

This challenge tests the ability to:

- Recognize Base58 encoded data.
- Identify Base32 from its alphabet and padding.
- Recognize Base45 from its distinctive character set.
- Identify ROT13 from recognizable plaintext.
- Reverse multiple layers of common encodings.
- Use CyberChef to test encoding hypotheses quickly.

## Conclusion

This is a multi-layer encoding challenge rather than a cryptographic attack. Each individual transformation is straightforward, but the solver must correctly identify the layers and reverse them in the right order.

The intended solve path is:

```text
Base58 → Base32 → Base45 → ROT13
```

which ultimately reveals:

```text
NullOrigin{5y57em_m34ns_3Lv1sh}
```
