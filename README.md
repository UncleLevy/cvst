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

## Demo mode vs. real scanning

By default (`CVST_USE_NMAP=False`) scans produce **simulated findings**, labelled `[SIMULATED]`, so you can exercise the whole workflow safely. To run real Nmap service discovery, install [Nmap](https://nmap.org/download.html), put it on your `PATH`, and set `CVST_USE_NMAP=True`.

**Only scan systems you own or have explicit written permission to test.** Target values are validated (type-checked, no whitespace or leading dashes, IPv4 ranges capped at /16) before they can reach a scanner.

## API

| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/login/` | returns `access`, `refresh`, `user` (throttled: 10/min) |
| POST | `/api/auth/token/refresh/` | |
| GET | `/api/auth/me/` | |
| POST | `/api/auth/register/` | disabled unless `CVST_ALLOW_REGISTRATION=True`; always creates an analyst |
| CRUD | `/api/targets/` | delete is a soft delete |
| CRUD | `/api/scans/` | `POST …/{id}/restart/`, `GET …/{id}/summary/` |
| GET | `/api/vulnerabilities/` | filter by `scan`, `severity`, `service` |

Analysts see only their own targets, scans and findings; admins (role `admin` or superuser) see everything.

## Tests and checks

```bash
cd backend && python manage.py test
cd frontend && npm run build        # type-checks, then builds
```

## Roadmap

- Report generation (PDF) and risk prioritisation (`reports` app)
- NVD / CVE lookup and CVSS-based scoring
- Web application scan module
