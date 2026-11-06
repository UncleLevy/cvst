# CVST

Vulnerability scanning and triage platform: a Django REST API with JWT auth and Celery-driven scan jobs, and a React (Vite + TypeScript + Tailwind) dashboard.

```
cvst/
├── backend/    Django + DRF + Celery
│   ├── config/         settings, urls, celery
│   └── apps/           accounts, core, targets, scans, vulnerabilities, detection
├── frontend/   React + Vite + TypeScript + Tailwind (burgundy / grey / navy)
└── docker-compose.yml  PostgreSQL + Redis (optional)
```

## Quick start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env                # Windows: copy .env.example .env
# set DEBUG=True and a SECRET_KEY in .env

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver          # http://127.0.0.1:8000
```

With no database variables set, the backend uses SQLite. To use PostgreSQL, run `docker compose up -d` from the repo root and set the `DB_*` variables in `backend/.env`.

### Running scans

Scans run as Celery tasks, so you need Redis and a worker:

```bash
docker compose up -d redis
celery -A config worker -l info --pool=solo     # --pool=solo is required on Windows
```

No Redis handy? Set `CELERY_TASK_ALWAYS_EAGER=True` in `.env` to run scans inline (the request blocks until the scan finishes; development only). If the broker is unreachable, a new scan is marked **failed** with an explanatory message rather than hanging.

### Frontend

```bash
cd frontend
cp .env.example .env                # optional: change VITE_API_URL
npm install
npm run dev                         # http://localhost:5173
```

Sign in with the superuser you created.

## Frontend design

The UI follows the Base44 version of CVST: navy and wine palette, left sidebar layout, dashboard with stat cards, scan-status donut and severity mix, a Findings page with severity filters and search, a scan report page that live-polls while a scan runs, and a Targets page. Not ported: Google sign-in, MFA/OTP and password-reset email flows (they depend on the Base44 platform).

## Real scanning

Scans are **real by default** (`CVST_REAL_SCANS=True`):

| Module | What it does |
|---|---|
| Network discovery | Nmap `-sV --top-ports 100`: open ports, service/version detection, exposure findings (Telnet, RDP, SMB, exposed databases and so on) and a small built-in list of known-vulnerable versions with CVE IDs. Needs the `nmap` binary (`sudo apt install nmap`). |
| Web application | Non-intrusive HTTP checks: HTTPS/redirects, TLS certificate trust and expiry, security headers, cookie flags, version disclosure, TRACE, and a few exposed files (`/.git/HEAD`, `/.env`, `phpinfo`, `server-status`). No fuzzing or payload injection. |
| Full assessment | Both of the above. |

Every finding records what was observed (**evidence**), a **recommendation** and **references**. Click any finding to see them. Severity for exposure findings is a rating, not a CVSS score, so their CVSS shows "Not scored"; only CVE-matched findings carry a CVSS value.

Safeguards:
- Launching a scan requires ticking "I own this target or have written permission to test it" (stored on the scan).
- Loopback addresses are refused unless `CVST_ALLOW_LOOPBACK_TARGETS=True`, and link-local/cloud-metadata (169.254.x.x) addresses are always refused. Private LAN ranges are allowed. Web redirects are re-checked at every hop.
- Target values are validated (type-checked, no whitespace or leading dashes, IPv4 ranges capped at /16).

Set `CVST_REAL_SCANS=False` for demo mode: clearly labelled `[SIMULATED]` findings, nothing sent to the target. **Only scan systems you own or have explicit written permission to test.**

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/login/` | returns `access`, `refresh`, `user` (throttled: 10/min) |
| POST | `/api/auth/token/refresh/` | |
| GET | `/api/auth/me/` | |
| POST | `/api/auth/register/` | disabled unless `CVST_ALLOW_REGISTRATION=True`; always creates an analyst |
| CRUD | `/api/targets/` | delete is a soft delete |
| GET | `/api/auth/config/` | public; `{registration_enabled}` so the UI can show or hide "Create one" |
| CRUD | `/api/targets/` | delete is a soft delete |
| CRUD | `/api/scans/` | `POST` needs `authorization_confirmed: true`; `POST …/{id}/restart/`, `GET …/{id}/summary/` |
| GET | `/api/scans/stats/` | `{total, active, completed, failed}` for the dashboard |
| GET | `/api/vulnerabilities/` | filter by `scan`, `severity`, `service`; `?search=` over title, CVE, description, service |
| GET | `/api/vulnerabilities/cve/<CVE-ID>/` | NVD lookup: description, CVSS score/vector, references |
| POST | `/api/vulnerabilities/<id>/enrich/` | refresh a finding's CVSS and references from the NVD |
| GET | `/api/reports/scans/<id>/` | prioritised report data (completed scans) |
| GET | `/api/reports/scans/<id>/pdf/` | downloadable PDF report |
| GET | `/api/vulnerabilities/stats/` | `{total, by_severity}`; optional `?scan=<id>` |

List endpoints accept `?page_size=` (default 20, max 200).

Analysts see only their own targets, scans and findings; admins (role `admin` or superuser) see everything.

## Tests and checks

```bash
cd backend && python manage.py test
cd frontend && npm run build        # type-checks, then builds
```

## Running scans

By default (`CVST_SCAN_RUNNER=thread`) scans run inside the Django process, so you only need `python manage.py runserver`: no Redis, no worker. For production set `CVST_SCAN_RUNNER=celery` and run Redis plus `celery -A config worker -l info` (add `--pool=solo` on Windows).

## Reports, scoring and NVD

- **Risk prioritisation.** Every finding gets a 0-100 risk score: the CVSS base score x10 (or a nominal estimate by severity for exposure findings that have no CVSS), +10 for a known CVE, +5 for services that give direct control or data when exposed. Scores map to **P1** fix immediately (85+), **P2** fix urgently (65+), **P3** plan a fix (35+), **P4** monitor. Findings lists are sorted by risk.
- **CVSS scoring.** A built-in CVSS v3.0/v3.1 calculator turns a vector string into a base score and severity (checked against published scores).
- **NVD / CVE lookup.** Uses the NVD CVE API 2.0 (cached 24h; optional `NVD_API_KEY` (free, request one at https://nvd.nist.gov/developers/request-an-api-key) for a higher rate limit). Scans refresh CVSS data for CVE findings and match detected product versions to CVEs through their CPE; those matches are labelled as needing verification, since vendors backport fixes. NVD being unreachable never fails a scan. In the UI use **NVD lookup** on the Findings page, or **Refresh from NVD** inside a finding.
- **PDF reports.** On a completed scan, **PDF report** downloads an executive summary, a ranked remediation table and per-finding detail (evidence, fix, references). `GET /api/reports/scans/<id>/` returns the same prioritised data as JSON.
- **Web application scan module.** See "Real scanning" above.

## Roadmap

- Scheduled and recurring scans
- Authenticated web scanning and active injection tests (opt-in)
- Report branding and per-target history comparison
