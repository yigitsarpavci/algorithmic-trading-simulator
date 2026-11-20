# Security Policy

## Supported versions
Only the latest commit on `main` receives security fixes.

## Reporting a vulnerability
Please **do not open a public issue** for security problems. Use GitHub's private reporting instead:
**Security tab → "Report a vulnerability"** on this repository.

I aim to acknowledge reports within a few days. This is a personal portfolio project, so there is no bug bounty, but responsible reports are appreciated and will be credited if you wish.

## What is already automated
- CodeQL code scanning, Dependabot alerts/updates and secret scanning with push protection are enabled.
- Secrets are read from environment variables (see `.env.example`); no real credentials are committed.
