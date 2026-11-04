# XYZ Technologies Limited: production website (Django)

Six pages (Home, About, Services, Products, Projects, Contact) with all content
managed from an admin dashboard, a secure contact form, and a deployable setup.

## Architecture

```
Browser
  |  HTTPS
  v
Host / reverse proxy (TLS, domain)
  |
  v
gunicorn (3 workers) -> Django 5.2+
  |-- WhiteNoise ........ serves compressed, cache-busted static files
  |-- Pages ............. templates fed from the database
  |-- /contact/send/ .... validates, saves, emails (background thread)
  |-- /admin/ ........... content + message management
  |-- /healthz/ /sitemap.xml /robots.txt
  v
PostgreSQL (production)  |  SQLite (local development)
```

```
config/settings/   base.py (shared), dev.py (local), prod.py (secure, PostgreSQL)
website/           public pages: models, views, forms, admin, emailing, middleware, tests
accounts/          client portal: signup, login, tickets, profile, emails, tests
website/management/commands/   seed_content, test_email
templates/         base.html, six pages, partials/, 404.html, 500.html
static/            css/, js/, images/
Dockerfile, docker-compose.yml, requirements*.txt, .env.example
```

## Database

| Table | Purpose |
|-------|---------|
| SiteSettings | company name, banner text, about text, phone, email, address, hours, map, social links (one row) |
| Stat, Service, Product, Project, Testimonial, TeamMember, Value, Milestone | page content, each with `order` and `is_published` |
| User (Django) + Profile | client accounts (email is the username), phone, company, verification and lockout fields |
| SupportTicket, TicketReply | portal support requests and the conversation on each |
| ContactMessage | every enquiry: details, status (new/read/replied), IP, email sent or error |

## Run locally (Windows PowerShell)

Open PowerShell INSIDE this folder (run `dir` and check you can see `manage.py`):

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations website accounts
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_content
python manage.py runserver
```

Website: http://127.0.0.1:8000  Admin: http://127.0.0.1:8000/admin/

Commit the files created in `website/migrations/` and `accounts/migrations/` to version control.

Run the automated tests any time: `python manage.py test`

## Client portal (login and signup)

Customers use `/account/`; staff use `/admin/`. They are separate on purpose.

- **Sign up:** email, name and a strong password. The account stays inactive until the
  person clicks the link emailed to them (set `ACCOUNTS_REQUIRE_EMAIL_VERIFICATION=False`
  to skip this while testing).
- **Log in:** by email. 5 wrong passwords lock the account for 15 minutes. Staff can
  unlock or activate users from Admin > Users (actions menu).
- **Password reset and change**, both by email, links valid for 24 hours.
- **Support requests:** clients open a request, follow the conversation and reply.
  You get an email for each new request or client reply. Reply from Admin > Support
  tickets: the client is emailed automatically and the status moves to "In progress".
- Only the owner can open their own tickets (anyone else gets a 404).

While testing locally, emails appear in the terminal running `runserver`, including
the confirmation and reset links. Set `SITE_URL` in `.env` so those links point to the
right address.

Make a staff user for the admin with `python manage.py createsuperuser`. Client
accounts and staff accounts are both "users"; only staff (is_staff) can enter /admin/.

## Edit content (no code needed)

Log in to the admin. "Site settings" holds phone, email, address, hours and the
Google Maps embed. Services, Products, Projects, Testimonials, Team, Values and
Milestones can be added, reordered (change `order`) or hidden (untick `published`).
`seed_content` adds SAMPLE text: replace it with your real information.

## Contact messages and email

Every message is saved first, so none is ever lost. The email is then sent in the
background. In Admin > Contact messages you can see whether the email was sent, read
the exact error if it failed, and use the action "Resend notification email".

Test your email settings and see the exact problem:

```powershell
python manage.py test_email
```

For Gmail use an App Password (Google Account > Security > 2-Step Verification >
App passwords). Put MAIL_TO, EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in `.env`,
then restart the server.

## Security built in

- HTTPS redirect, HSTS, secure cookies, no clickjacking, no content sniffing
- Content-Security-Policy (no inline scripts or styles are allowed)
- CSRF protection on the form, honeypot field, rate limit per visitor (5 per 10 minutes)
- Login lockout, email verification, 24-hour reset links, strong password rules (10+ characters)
- Ticket access checks: a client can only ever open their own requests
- Input validation on server and browser
- Secrets only in environment variables; production refuses to start without them
- Optional hidden admin address: set `ADMIN_URL=manage-xyz/`

## Deploy

### Option A: Docker on any server

```bash
cp .env.example .env        # fill in SECRET_KEY, ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS, email
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py seed_content
```

`docker-compose.yml` is for a local production-like test (HTTP, FORCE_HTTPS=False).
On a real server put it behind HTTPS (for example Caddy or Nginx), remove the
FORCE_HTTPS override and use a strong database password.

### Option B: a managed host (Render, Railway, Fly.io and similar)

1. Create a PostgreSQL database and copy its URL into `DATABASE_URL`.
2. Create a web service from this project. Build command:
   `pip install -r requirements-prod.txt && python manage.py collectstatic --noinput`
   Start command:
   `python manage.py migrate --noinput && gunicorn config.wsgi:application`
3. Set `DJANGO_SETTINGS_MODULE=config.settings.prod`, `SECRET_KEY`, `ALLOWED_HOSTS`,
   `CSRF_TRUSTED_ORIGINS` (with https://), `TRUST_PROXY=True` and the email variables.
4. Point your domain at the service and enable HTTPS.
5. Run `createsuperuser` and `seed_content` once from the host's shell.
6. Set the health check path to `/healthz/`.

### Before going live

```bash
python manage.py check --deploy
python manage.py test
```

- Replace sample text and placeholder phone and address in the admin
- Raise `HSTS_SECONDS` to 31536000 once HTTPS works everywhere
- Back up PostgreSQL regularly (`pg_dump`) and keep `.env` private
- Free uptime monitoring on `/healthz/` (for example UptimeRobot)

## Known limits (next steps)

- Signup and password reset can still be abused to send emails to strangers: add a CAPTCHA
  (Cloudflare Turnstile or hCaptcha) before a high-traffic launch.
- Optional two-factor login for staff accounts, and file attachments on tickets.

## Scaling up later

Move the background email to Celery and Redis, add a CDN in front of static files,
and add media uploads (project photos) with object storage.
