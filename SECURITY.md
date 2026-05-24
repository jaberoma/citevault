# Security Policy

## Reporting a vulnerability

Please **do not open a public issue** for security vulnerabilities.

Use [GitHub's private vulnerability reporting](../../security/advisories/new) to submit
a confidential report. Include a description of the issue, steps to reproduce, and the
potential impact.

Reports are handled on a **best-effort basis** — there is no guaranteed response time.
Security fixes are prioritised over other changes, but no specific timeline can be
committed to. This project is provided as-is (see [LICENSE](LICENSE)).

## Threat model

Citevault runs entirely on your local machine. The attack surface is:

- The Docker Compose stack (API, UI, Ollama) — all bound to localhost
- A SQLite database stored in a named Docker volume
- Evidence files you provide, mounted read-only

There is no cloud component, no user accounts, and no data leaves your machine.
