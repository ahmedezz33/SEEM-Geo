# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x  | ✅ Yes  |
| 1.0.x  | ⚠️ Critical fixes only |
| < 1.0  | ❌ No  |

## Reporting a Vulnerability

If you discover a security vulnerability, **please do not open a public GitHub issue**.

Instead, email **your-email@example.com** with:

1. A description of the vulnerability
2. Steps to reproduce
3. Potential impact
4. Suggested fix (if any)

You will receive a response within **5 business days** acknowledging the report. We will work with you to understand and resolve the issue, and will credit you in the release notes (unless you prefer to remain anonymous).

## Scope

The following are considered in-scope for security reports:

- Arbitrary code execution via project files or input data
- Path traversal in file handling
- Denial-of-service via malformed input
- Credential leakage in logs or outputs

Out of scope:

- Vulnerabilities in third-party dependencies (report upstream)
- Social-engineering attacks
- Physical attacks
