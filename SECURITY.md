# Security Policy

OmniDev is a **local-first** tool: the backend, frontend, and AI model all run
on your machine, and no data leaves it unless you connect a cloud provider
(Gemini) or cloud credentials (AWS). Security reports are taken seriously.

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.3.x   | ✅        |
| < 0.3   | ❌        |

## Reporting a vulnerability

**Please do not open a public issue for security vulnerabilities.**

Report privately through one of:

- GitHub's [private vulnerability reporting](https://github.com/himanshu748/omnidev/security/advisories/new)
  (Security → Report a vulnerability), or
- Email **jhahimanshu653@gmail.com** with the subject `OmniDev security`.

Please include: affected version, a description, reproduction steps, and the
impact. We aim to acknowledge within **72 hours** and to ship a fix or mitigation
for confirmed issues as promptly as possible. We'll credit you in the release
notes unless you prefer to remain anonymous.

## Scope and hardening

OmniDev already defends the areas most relevant to a local AI cockpit:

- **SSRF** — the Web Scraper and Site Preview validate every target URL and
  refuse loopback, private, link-local, reserved, and cloud-metadata addresses
  (`169.254.169.254`, `localhost`, `10/8`, `192.168/16`, etc.).
- **Destructive AWS actions** — the DevOps Agent shows the exact boto3 plan and
  requires explicit confirmation; `DEVOPS_READ_ONLY=1` refuses all mutations.
- **Code generation** — generated files are path/secret/npm-script validated and
  are **never executed** on the backend.
- **Secrets** — API error boundaries scrub secret-like values from responses.

Out of scope: issues requiring a compromised local machine or physical access,
and third-party services (Ollama, Gemini, AWS) themselves.
