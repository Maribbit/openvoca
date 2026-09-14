# Security Policy

## Supported Versions

Only the latest release is actively maintained with security updates.

| Version | Supported |
|---------|-----------|
| Latest  | Yes       |
| Older   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Open a [GitHub Security Advisory](https://github.com/Maribbit/openvoca/security/advisories/new) (preferred), or contact the maintainers directly.
3. Include a description of the vulnerability, steps to reproduce, and potential impact.

We will acknowledge the report within 48 hours and aim to provide a fix or mitigation within 7 days for critical issues.

## Scope

OpenVoca runs locally on the user's machine. The main security considerations are:

- **API key handling** — Keys are stored in the local SQLite database and never transmitted to third parties or included in exports.
- **LLM endpoint** — Users configure their own endpoint. OpenVoca does not proxy or log API traffic beyond what is needed for sentence generation.
- **Local data** — All vocabulary and settings data stays on the user's device.
