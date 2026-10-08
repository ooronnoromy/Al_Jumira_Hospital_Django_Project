# Deploy the hospital project to Railway

The repository includes a Docker build, Gunicorn startup, database migrations,
compressed static files, an HTTPS configuration, and a database health check.
Local `python manage.py runserver` continues to use your existing `.env`.

## Current Railway target

This checkout is linked to the `Al_Jumira_Hospital_Django_Project` service in
[devoted-serenity](https://railway.com/project/ea0d62a2-f58e-445a-b7fc-a55765567b67).
Production environment variables and a generated secret are saved in Railway.
The public domain is `aljumirahospitaldjangoproject-production.up.railway.app`.

Deployment is live on the Hobby plan. PostgreSQL and the `/data` upload volume
are attached. The local hospital database was imported into Railway; row counts
matched for all 42 tables. Existing administrator accounts were preserved.
The live login page, health endpoint, stylesheet, hospital logo, dashboard,
administrator portal, patient information, doctors, services, and advertisement
page were verified. Temporary verification sessions were removed.

Migration and health-check settings are also saved directly on the Railway
service. An explicit static-build command is saved as a fallback for Railway's
default builder. The app uses the private PostgreSQL connection; the temporary
public connection used for migration was removed.

A fresh local backup is stored under `.railway/backups/`, which is excluded
from Git, Docker builds, and CLI uploads. Deployment used `railway up` from this
checkout; it did not push these changes to GitHub. Use `railway up` for updates
from this checkout, or push the prepared code before using GitHub autodeploys.

## Railway setup

1. Create a Railway project and add a PostgreSQL service named `Postgres`.
2. Add this repository as an application service. Select the folder containing
   `manage.py`, `Dockerfile`, and `railway.json` as the service root.
3. Add an application volume mounted at `/data`. Set `ADVERTISEMENT_ROOT` below
   so uploaded advertisements survive redeployments.
4. Set these variables on the application service:

   ```dotenv
   DJANGO_ENV=production
   DJANGO_DEBUG=0
   DJANGO_SECRET_KEY=<your-new-random-secret>
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ADVERTISEMENT_ROOT=/data/advertisements
   WEB_CONCURRENCY=2
   ```

   Generate the secret locally with:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(64))"
   ```

   Use the Railway database credentials, not the local PostgreSQL password.
   Do not commit `.env`, database exports, or uploaded media.

5. Generate a public domain under the application's Networking settings.
   `RAILWAY_PUBLIC_DOMAIN` supplies the allowed host and trusted CSRF origin.
   For a custom domain, also set `DJANGO_ALLOWED_HOSTS=hospital.example.com`
   and `DJANGO_CSRF_TRUSTED_ORIGINS=https://hospital.example.com`.
6. Deploy. The Docker build collects static files; the pre-deploy command applies
   migrations; Gunicorn binds to Railway's `PORT`. `/healthz/` must return 200
   before Railway marks the deployment healthy.
7. Verify `/login`, a stylesheet, administrator login, patient workflows, and
   advertisement upload. Redeploy once to verify uploaded files persist.

The application trusts Railway's `X-Forwarded-Proto` HTTPS header. Use this
production configuration behind Railway's proxy. HSTS is enabled for the app's
domain; enable public HTTPS before serving it.
HSTS preload and inclusion of subdomains are intentionally not enabled; only
enable those if you control the domain and all its subdomains use HTTPS.

## Deploy from this computer with CLI

If Railway CLI is not installed, use `npx.cmd --yes @railway/cli` instead of
`railway` for each command on Windows:

```powershell
railway login
railway link
railway up
```

Link to the application service after configuring the database, volume, and
variables above. `.railwayignore` and `.dockerignore` exclude local secrets,
virtual environments, database exports, and uploaded advertisements.

## Existing hospital data

A new Railway database starts empty. Migration creates the schema, but does not
copy patients, accounts, or hospital records from your computer. Preserve a
backup and restore your local PostgreSQL database into the new Railway database
before using the application. Coordinate a final transfer while local writes
are stopped. Do not restore over a database that already contains live records.
Copy existing `assets/advertisements` into the volume's `/data/advertisements`
directory separately. Configure Railway database and volume backups.

For a fresh database, create the application's first administrator inside the
running service:

```bash
python manage.py admin_account USERNAME --email admin@example.com
```

This command prompts for a password. `createsuperuser` creates a Django admin
account; the hospital login uses the separate `admin_account` command.
