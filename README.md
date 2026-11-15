# Cyber Defense Lab — Safe Red/Blue Training Simulator

An **isolated educational simulator** with Flask, SQLAlchemy, JWT
authentication, React and Vite. Learners register practice accounts,
generate preset **synthetic** security events and explore a private
event timeline with severity counts.

No real network capture, attack execution, intrusion detection, Suricata,
Grafana or operational SIEM integration exists. Team selection (red/blue)
is a training preference, **not** administrator authorization.

## Run locally in Windows PowerShell

Terminal 1 (Python 3.11+):

```powershell
git clone https://github.com/rainrunner20/Cyber-Defense-Lab.git
cd Cyber-Defense-Lab
py -m venv .venv
.\.venv\Scripts\python -m pip install -r backend/requirements.txt
$env:JWT_SECRET_KEY = & .\.venv\Scripts\python -c "import secrets; print(secrets.token_urlsafe(48))"
cd backend
..\.venv\Scripts\python app.py
```

This defaults to a local SQLite database in Flask's instance directory.
No external service or PostgreSQL account is needed.

In a second terminal:

```powershell
cd Cyber-Defense-Lab/frontend
npm ci
npm run dev
```

Open http://localhost:5173, register a practice account and sign in.
The JWT is held in browser memory and expires after one hour; use example
credentials, not real passwords.

## Optional local Docker

Copy `.env.example` to `.env`, fill in a unique PostgreSQL password and
random JWT secret privately, then run `docker compose up --build`.
Docker ports bind to 127.0.0.1, not public network interfaces.

## Tests

```powershell
py -m unittest discover -s backend/tests -v
cd frontend
npm ci
npm run build
```

GitHub Actions tests Python 3.11 and 3.12 plus the Vite build. Regression
tests cover hashed passwords, duplicate and invalid accounts, JWT access,
private per-user event lists, synthetic event types and CORS limits.

## Scope and roadmap

The interface visualizes local event metadata only, not live alerts.
SQLite is the simplest offline path; Docker offers PostgreSQL for learning.
Before a hosted release, add migrations, login rate limiting, HTTPS,
retention policies, monitoring, and a wider security review.

The previous repository had incomplete Flask source, a hardcoded JWT secret
and an unimplemented SIEM feature list. This milestone is a working training
baseline, **not a public security product**.
