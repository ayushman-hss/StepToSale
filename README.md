# StepToSale

<!-- TODO: one-paragraph description of what this project actually does.
     e.g. "A marketplace platform for X. Sellers list Y, buyers browse Z,
     payments handled via W." Keep it to 2–3 sentences. -->

A full-stack web application with a FastAPI + PostgreSQL backend and a
modern JavaScript frontend.

---

## Stack

| Layer         | Technology                                    |
| ------------- | --------------------------------------------- |
| Backend       | Python 3.11+, FastAPI, SQLModel, Alembic       |
| Database      | PostgreSQL 15+ (via `psycopg` 3)               |
| Frontend      | Node.js 18+, Next.js                           |
| Auth          | <!-- TODO: JWT? session cookies? Auth0? -->    |
| Package mgmt  | `pip` / `venv` (backend), `npm` (frontend)     |

---

## Project structure

```
StepToSale/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py         # pydantic-settings; reads .env
│   │   ├── db.py             # SQLModel engine, init_db(), get_session()
│   │   ├── models.py         # SQLModel table definitions
│   │   └── main.py           # FastAPI app entry point
│   ├── alembic/              # migrations
│   │   ├── env.py
│   │   └── versions/
│   ├── alembic.ini
│   ├── .env                  # NOT committed
│   └── .env.example          # committed; copy to .env and fill in
├── frontend/
│   ├── package.json
│   └── ...
├── Makefile                  # convenience targets (see below)
├── .gitignore
└── README.md
```

---

## Prerequisites

Install these before doing anything else:

- **Python 3.11+** — https://www.python.org/downloads/ (check "Add to PATH" on Windows)
- **Node.js 18+** — https://nodejs.org/
- **PostgreSQL 15+** — https://www.postgresql.org/download/
- **Git** — https://git-scm.com/

Optional:

- **GNU Make** — convenience wrapper around the common commands.
  Not installed by default on Windows; see [Running the project](#running-the-project).
  - Windows: `winget install ezwinports.make`
  - macOS: `brew install make`
  - Linux: `sudo apt install make` (or your distro's equivalent)

You do **not** need Docker for local development. The default setup runs
Postgres natively.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/ayushman-hss/StepToSale.git
cd StepToSale
```

### 2. Create the database and role

Postgres must have a role and database matching what's in `backend/.env`
(defaults below match the example file).

Open `psql` as the Postgres superuser:

```bash
# macOS / Linux
sudo -u postgres psql

# Windows (PowerShell, from an elevated prompt)
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres
```

Then:

```sql
CREATE USER footfall WITH PASSWORD 'footfall' LOGIN;
CREATE DATABASE footfall OWNER footfall;
\c footfall
GRANT ALL ON SCHEMA public TO footfall;
ALTER SCHEMA public OWNER TO footfall;
\q
```

> **Why the last two grants?** Postgres 15+ no longer lets non-owners write
> to the `public` schema by default. Without these, Alembic will fail with
> "permission denied for schema public" even after auth succeeds.

If you already have a role/database and just need to reset the password:

```sql
ALTER USER footfall WITH PASSWORD 'footfall';
```

See [Troubleshooting → Postgres auth](#postgres-password-authentication-failed)
if you don't know the `postgres` superuser password.

### 3. Backend

```bash
cd backend
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create your `.env` from the example:

```bash
cp .env.example .env       # macOS / Linux
copy .env.example .env     # Windows (PowerShell)
```

Edit `backend/.env` and set at minimum:

```env
DATABASE_URL=postgresql+psycopg://footfall:footfall@localhost:5432/footfall
```

<!-- TODO: list any other required env vars your settings.py reads
     (SECRET_KEY, JWT_EXPIRY, CORS_ORIGINS, third-party API keys, etc.) -->

Verify the connection works before going further:

```bash
python -c "from sqlmodel import create_engine, text; from app.config import settings; e = create_engine(settings.database_url); c = e.connect(); print(c.execute(text('select current_user, current_database()')).one()); c.close()"
```

Expected output:

```
('footfall', 'footfall')
```

If this fails, fix it now — Alembic will fail with a much uglier error.

### 4. Run migrations

From `backend/`, with the venv activated:

```bash
alembic upgrade head
```

### 5. Frontend

```bash
cd frontend
npm install
```

<!-- TODO: create frontend/.env.local if the frontend needs to know
     the backend URL, e.g. NEXT_PUBLIC_API_URL=http://localhost:8000 -->

---

## Running the project

The `Makefile` provides shortcuts. **On Windows without `make` installed,
run the underlying commands directly** — the table below shows both.

| What you want        | With `make`      | Without `make` (raw command)                              |
| -------------------- | ---------------- | --------------------------------------------------------- |
| Start Postgres       | `make db-up`     | *(only needed if using Docker; skip for native Postgres)* |
| Apply migrations     | `make migrate`   | `cd backend && alembic upgrade head`                      |
| Run backend (dev)    | `make backend`   | `cd backend && uvicorn app.main:app --reload`             |
| Run frontend (dev)   | `make frontend`  | `cd frontend && npm run dev`                              |

Typical workflow:

1. Terminal 1: start the backend
2. Terminal 2: start the frontend
3. Open http://localhost:3000 (frontend) — it talks to http://localhost:8000 (backend)

<!-- TODO: confirm the actual ports. uvicorn defaults to 8000; Next.js to 3000.
     Update if your Makefile or config overrides them. -->

---

## Database migrations

Alembic lives in `backend/alembic/`. All migrations go in
`backend/alembic/versions/` and **must be committed to Git** — they are part
of your source, not build artifacts.

### Create a new migration after changing models

```bash
cd backend
alembic revision --autogenerate -m "short description of change"
```

Then **open the generated file and read it**. Autogenerate is helpful but
imperfect — it misses column renames, enum changes, and some server defaults.
Edit it by hand if needed.

### Apply migrations

```bash
alembic upgrade head
```

### Roll back one migration

```bash
alembic downgrade -1
```

### See history

```bash
alembic history
alembic current
```

### How Alembic sees your models

`alembic/env.py` must import your models so SQLModel registers the tables
before autogenerate runs. If autogenerate produces an empty migration, the
most likely cause is a missing import in `env.py`. See `backend/app/db.py`
for the `from . import models  # noqa: F401` pattern used to force registration.

---

## Environment variables

All backend config lives in `backend/.env` (gitignored). Copy
`backend/.env.example` to get started. Do **not** commit `.env`.

| Variable       | Required | Default                                                          | Notes                  |
| -------------- | -------- | ---------------------------------------------------------------- | ---------------------- |
| `DATABASE_URL` | yes      | `postgresql+psycopg://footfall:footfall@localhost:5432/footfall` | Full SQLAlchemy URL    |
| <!-- TODO -->  |          |                                                                  |                        |

---

## Troubleshooting

### `make: command not found` (Windows)

`make` isn't installed on Windows by default. Either install it
(`winget install ezwinports.make`) or run the raw commands from the table in
[Running the project](#running-the-project). The latter is usually less
painful — Windows `make` struggles with Unix-style Makefile recipes.

### Postgres: `password authentication failed`

The role exists but the password Postgres has on file doesn't match what's in
your connection string. Fix:

1. Log in as superuser:
   - **macOS:** `sudo -u postgres psql`
   - **Windows:** `& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres`
   - **Linux:** `sudo -u postgres psql`
2. Run: `ALTER USER footfall WITH PASSWORD 'footfall';`
3. Retry your connection.

If you don't know the `postgres` superuser password on Windows:

1. Edit `C:\Program Files\PostgreSQL\17\data\pg_hba.conf` **as Administrator**
   (launch Notepad from an elevated PowerShell:
   `notepad "C:\Program Files\PostgreSQL\17\data\pg_hba.conf"`).
2. Change `scram-sha-256` → `trust` on the two `host all all` lines for
   `127.0.0.1/32` and `::1/128`.
3. Restart: `Restart-Service postgresql-x64-17` (elevated PowerShell).
4. `psql -U postgres` — no password prompt.
5. `ALTER USER postgres WITH PASSWORD 'your_new_password';`
   and `ALTER USER footfall WITH PASSWORD 'footfall';`
6. **Revert** `pg_hba.conf` back to `scram-sha-256`.
7. Restart the service again.

> Windows gotcha: if you edit `pg_hba.conf` from a non-elevated Notepad,
> Windows silently redirects the save to
> `%LOCALAPPDATA%\VirtualStore\Program Files\PostgreSQL\17\data\`.
> The file *looks* saved, but Postgres reads the original. Always edit from
> an elevated process.

### Alembic: empty autogenerate migration

SQLModel only registers a table when its class is *defined* (imported at
least once). If `alembic/env.py` doesn't import your `models` module,
`create_all` and autogenerate see zero tables. Make sure `env.py` triggers
`from app import models` (directly or via `app.db`'s `init_db`).

### GitHub: `GH007: Your push would publish a private email address`

Git is configured with an email that GitHub knows is private. Two fixes:

- **Quick:** uncheck "Block command line pushes that expose my email" at
  https://github.com/settings/emails, push, then re-enable. Email ends up in
  the commit history.
- **Recommended:** copy your `noreply` address from the same settings page,
  then:
  ```bash
  git config --global user.email "12345678+yourusername@users.noreply.github.com"
  git commit --amend --reset-author --no-edit
  git push
  ```
  See [Git identity](#git-identity) below.

### Git: commits show the wrong author

Git records the author from your local config at commit time, not from your
GitHub login. To check what's set:

```bash
git config --list --show-origin | grep user\.
```

To fix a single repo:

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

To fix a bad commit that's already on GitHub, amend and force-push:

```bash
git commit --amend --reset-author --no-edit
git push -f
```

If multiple commits are affected, the fastest clean fix for a young repo is
to wipe local history and re-commit:

```bash
rm -rf .git           # or Remove-Item -Recurse -Force .git on Windows
git init
git branch -M main
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/ayushman-hss/StepToSale.git
git push -f -u origin main
```

---

## Git identity

Before your first commit, set:

```bash
git config --global user.name  "Your Name"
git config --global user.email "you@example.com"
```

Using the `noreply` email GitHub provides keeps your real address out of
public commit metadata while still attributing commits to your account.

---

## Development workflow

- `main` is the stable branch. Don't commit to it directly once the project
  has more than one contributor.
- Feature branches: `git checkout -b feature/short-name`
- Open a pull request against `main` when ready to merge.
- Run `alembic revision --autogenerate` **and inspect the output** before
  applying schema changes.
- Commit migrations together with the model change that caused them.

---

## Security notes

- **Never commit `.env`.** It's in `.gitignore`. If you accidentally commit
  it, rotate every credential it contains — GitHub indexes new repos within
  minutes and bots scrape for leaked keys.
- Use a `noreply` GitHub email for commits.
- Local dev credentials (`footfall:footfall`) are fine for a laptop, **not**
  fine for anything reachable from the internet.
- Before deploying: replace all secrets in `.env`, turn off `echo=True` on
  the SQLAlchemy engine if you ever enabled it, and use a managed Postgres
  with proper role separation.

---

## License

<!-- TODO: add a LICENSE file and reference it here.
     MIT is the usual choice for personal projects:
     https://choosealicense.com/licenses/mit/ -->
