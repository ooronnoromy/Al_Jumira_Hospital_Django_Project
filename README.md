# Hospital Management System — Django + PostgreSQL migration

This is a Django and PostgreSQL hospital management application covering patient registration, permissions, reports, prescriptions, admissions, pathology, pharmacy, accounts, queues, and advertisement uploads. Existing Jinja templates are supported through a Django compatibility layer while business workflows are migrated incrementally to native Django code.

## 1. Prepare the project

### Windows PowerShell

```powershell
cd hospital_management_django
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### Linux/macOS

```bash
cd hospital_management_django
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`. Change all passwords and the Django secret key.

## 2. Start PostgreSQL

With Docker Desktop installed:

```bash
docker compose --env-file .env up -d db
```

Or create the database manually in PostgreSQL using the same database name, user, password, host, and port from `.env`.

## 3. Create the PostgreSQL tables

```bash
python manage.py migrate
```

## 4. Copy your existing SQLite data (optional)

Put the old `hospital.db` in the project folder, then run:

```bash
python scripts/migrate_sqlite_to_postgres.py hospital.db --clear
```

The script preserves original integer IDs and existing Werkzeug password hashes.

## 5. Collect static files

```bash
python manage.py collectstatic --noinput
```

## 6. Run the application

For Railway deployment, see [RAILWAY.md](RAILWAY.md).

```bash
python manage.py runserver
```

`manage.py` automatically uses `.venv` or `venv` when invoked with system
Python. An already activated virtual environment is respected. Database
credentials must be configured in `.env`; use `.env.example` as the template.

On Windows, the recommended launcher always uses the project's virtual
environment, verifies PostgreSQL, applies pending migrations, and starts the
server:

```powershell
.\start_server.cmd
```

Open `http://127.0.0.1:8000/login`.

Administrator credentials are stored as password hashes in PostgreSQL. Create
the first administrator, or reset an existing administrator, with:

```bash
python manage.py admin_account USERNAME --email admin@example.com
```

The command prompts for the password without displaying it. On Windows, use
`.venv\Scripts\python.exe` instead of `python` if the virtual environment is not
activated.

## Development check without PostgreSQL

The project includes a temporary SQLite mode only for smoke testing:

```powershell
$env:USE_SQLITE="1"
python manage.py migrate
python manage.py runserver
```

On Linux/macOS use `USE_SQLITE=1 python manage.py migrate`.

## Architecture

- `hospital/legacy_views.py` — converted Flask business logic and all route handlers.
- `hospital/compat.py` — Flask request/session/response and SQLite-SQL compatibility layer on top of Django/PostgreSQL.
- `hospital/models.py` — Django schema for the original 29 application tables.
- `hospital/urls.py` — Django URL mappings generated from the original route decorators.
- `scripts/migrate_sqlite_to_postgres.py` — old-data importer.
- `hospital/migrations/0002_postgresql_compat.py` — PostgreSQL helper functions used by legacy date/report SQL.

## Security work required before production

CSRF protection is enabled for all HTML forms and JavaScript write requests.

1. Set `DJANGO_DEBUG=0`, configure HTTPS, secure cookies, backups, and restricted database/network access.
2. Replace all example secrets and passwords in `.env`.
3. Remove the compatibility root admin after creating a database-backed administrator.
4. Gradually rewrite `legacy_views.py` raw SQL into Django ORM/services and add automated tests before changing billing behavior.

## Validation

Run the PostgreSQL-backed verification suite with:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
```

The suite checks authentication and CSRF behavior, every non-parameterized route, static assets and rendered links, patient/doctor/service creation, linked-record deletion safety, and data-backed detail, API, and print routes.
