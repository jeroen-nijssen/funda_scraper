# Security Policy

## Supported versions

Woningradar is a self-hosted hobby project. Only the latest release published
from the `main` branch receives security fixes.

| Version | Supported |
| --- | --- |
| Latest release / `main` | Yes |
| Older tags | No |

## Reporting a vulnerability

Please do **not** open a public issue for a security problem.

Use GitHub's private vulnerability reporting instead: go to the
[Security tab](https://github.com/jeroen-nijssen/funda_scraper/security) and
choose **Report a vulnerability**. This opens a private advisory visible only to
the maintainer.

What to expect:

- Acknowledgement within roughly a week. This is a spare-time project, so please
  be patient.
- If the report is valid, a fix and a published advisory crediting you unless you
  prefer otherwise.
- If it is out of scope, an explanation of why.

## Hardening notes for operators

The default deployment is built for convenience on a trusted home network, not
for exposure to the internet. Before running it anywhere else:

- **Change the Kanboard credentials.** The stack ships with `admin`/`admin`.
  Change the password in Kanboard's web UI and update `KANBAN_PASSWORD` in `.env`.
- **Never expose port 8080 to the internet.** Kanboard would be reachable by
  anyone, and it holds your saved listings. Keep it on the local network or
  behind a VPN or authenticating reverse proxy.
- **Port 8000 is unauthenticated.** The health and status endpoints expose worker
  statistics and error messages. Do not publish it either.
- **`.env` holds credentials in plain text.** It is git-ignored; keep it that
  way. For anything beyond a home setup use Docker secrets or a secrets manager.
- **Kanboard data lives in a Docker volume** (`kanboard_data`, SQLite). Back it
  up if the board matters to you, and remember it is unencrypted at rest.
