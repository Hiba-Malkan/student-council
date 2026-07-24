# Local Development Guide

This document describes how to set up and run the Student Council Management System in a local development environment.

## System Requirements

- macOS, Linux, or Windows with WSL2
- Python 3.13 or later
- Node.js 18 or later
- PostgreSQL 12 or later
- Redis (latest stable release)
- Git

Minimum hardware: 4GB RAM, dual-core 2GHz processor, 50GB free disk space.

Verify installed versions:

```bash
python3 --version
node --version
psql --version
redis-cli --version
git --version
```

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Hiba-Malkan/student-council.git
cd student-council
```

### 2. Create and activate a virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

On Windows, activate with `venv\Scripts\activate`.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `backend/.env`:

```env
SECRET_KEY=django-insecure-your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_council_db
DB_USER=hiba
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_password
DEFAULT_FROM_EMAIL=your_email@example.com
SITE_URL=http://localhost:8000
```

**Note:** `DB_USER` must match an existing PostgreSQL role, not necessarily your operating system username. If migration commands fail with a "role does not exist" error, run `psql -l` to confirm the correct role before proceeding.

### 5. Set up the database

```bash
createdb student_council_db
python manage.py migrate
python manage.py createsuperuser
```

Newly registered users are assigned the Student role by default. Superuser accounts have administrative access but are not automatically assigned a council role. Only users with a C-Suite role (President, Vice President, Secretary, Treasurer) can assign roles to other users, so the superuser account's role must be set manually before role assignment can occur through the application.

### 6. Configure roles

The system defines the following roles:

| Role | Permissions |
|---|---|
| Student | Default role. View clubs and announcements, sign up for competitions and clubs. No create/edit access. |
| Captain | Manage competition signups and view participant details. |
| Class Representative | Access to class-specific organizational data. |
| C-Suite (President, VP, Secretary, Treasurer) | Full administrative access: create/edit announcements, schedule meetings, edit the duty roster, manage competitions, view discipline records, assign roles. |

To assign a role via Django admin:

1. Navigate to `http://localhost:8000/admin/`
2. Log in with superuser credentials
3. Select "Users" from the sidebar
4. Select the target user
5. Set the "Role" field
6. Save

To assign a role via the API (requires C-Suite permissions):

```bash
curl -X POST http://localhost:8000/api/accounts/{user_id}/assign_role/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_id": 2}'
```

Retrieve available role IDs:

```bash
curl http://localhost:8000/api/roles/
```

Requests to this endpoint from users without C-Suite status return `403 Forbidden`.

### 7. Verify the database schema

```bash
psql -U hiba -d student_council_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
```

### 8. Install frontend dependencies

```bash
cd ../frontend
npm install
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

For automatic rebuilds during development, use watch mode:

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch
```

## Running the Application

Local development requires four concurrent processes, each run in a separate terminal.

**Terminal 1 — Django development server**

```bash
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

The server auto-reloads on code changes. Request logs are printed to this terminal.

**Terminal 2 — Celery worker**

```bash
celery -A student_council worker --loglevel=info
```

Processes background tasks, primarily email delivery.

**Terminal 3 — Celery Beat**

```bash
celery -A student_council beat --loglevel=info
```

Executes scheduled tasks. Notifications are dispatched at 7:00 AM and 4:00 PM daily.

**Terminal 4 — Redis**

```bash
redis-server
```

Serves as the message broker between Django and Celery.

**Important:** All four processes must remain running for the application to function correctly. If the Celery worker or Celery Beat terminal is closed, Django continues to run without error, but background tasks — including notification emails — silently stop processing.

Alternatively, all services can be started from a single script:

```bash
#!/bin/bash
cd backend
source venv/bin/activate

python manage.py runserver &
celery -A student_council worker --loglevel=info &
celery -A student_council beat --loglevel=info &
redis-server &

wait
```

Run with `bash start_dev.sh`. This approach interleaves log output from all services in a single terminal, which can make debugging more difficult. The four-terminal approach is recommended when working on Celery-related functionality.

## Development Workflow

### Templates and stylesheets

HTML templates in `frontend/templates/` reload automatically; no build step is required. CSS changes require rebuilding Tailwind output:

```bash
cd frontend
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch
```

### Backend code changes

Changes to models, views, and serializers are picked up automatically by Django's development server. No restart is required.

### Creating and applying migrations

```bash
python manage.py makemigrations
```

Review the generated migration file before applying it:

```bash
cat backend/accounts/migrations/000X_*.py
```

```bash
python manage.py migrate
python manage.py showmigrations
```

### Example: adding a model field

Edit `backend/clubs/models.py`:

```python
class Club(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, default='')
```

```bash
python manage.py makemigrations clubs
python manage.py migrate
```

Update the corresponding serializer in `backend/clubs/serializers.py`:

```python
class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ['id', 'name', 'description', 'location']
```

Verify the change via the API:

```bash
curl http://localhost:8000/api/clubs/
```

## API Testing

```bash
curl http://localhost:8000/api/clubs/
curl "http://localhost:8000/api/clubs/?status=active"
curl "http://localhost:8000/api/clubs/?search=coding"
curl "http://localhost:8000/api/clubs/?page=2"
```

Authenticate to obtain a token:

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

Use the access token for protected endpoints:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/accounts/me/
```

### VS Code REST Client

Install the REST Client extension and create a `test.http` file:

```http
### Get all clubs
GET http://localhost:8000/api/clubs/

### Login
POST http://localhost:8000/api/accounts/login/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

### Get current user
GET http://localhost:8000/api/accounts/me/
Authorization: Bearer YOUR_TOKEN_HERE

### Get user duties
GET http://localhost:8000/api/duty-roster/
Authorization: Bearer YOUR_TOKEN_HERE
```

Requests can be executed individually by selecting "Send Request" above each block.

### Postman

Create a collection for the API, with one request per endpoint. Bearer tokens are configured under the Authorization tab per request or per collection.

## Managing Signups

Competition and club signups are managed through `/competitions/signups/` and `/clubs/signups/` respectively. Each page displays signup details — name, email, phone, team assignment (competitions only), and any accompanying message — filterable by competition or club.

Deleting a signup opens a confirmation modal, styled with a white background and dark text in light mode, and a dark gray background with white text in dark mode. The modal combines inline styles for structural properties (padding, font size, borders) with Tailwind `dark:` classes for color variants; this pattern is documented in `STYLING_GUIDE.md`.

Signup lists are paginated at 10 entries per page. The full text of a signup message is viewable via the message modal, which supports scrolling for longer content.

## Database Management

```bash
psql -U hiba -d student_council_db -c "\dt"
psql -U hiba -d student_council_db -c "\d clubs_club"
psql -U hiba -d student_council_db -c "SELECT * FROM accounts_user;"
psql -U hiba -d student_council_db
```

Interactive shell commands:

```
\dt                          List tables
\d clubs_club                Describe table structure
SELECT * FROM clubs_club;    Run a query
\q                           Exit
```

### Backup and restore

```bash
pg_dump -U hiba student_council_db > backup.sql
pg_dump -U hiba student_council_db | gzip > backup.sql.gz

psql -U hiba student_council_db < backup.sql
gunzip -c backup.sql.gz | psql -U hiba student_council_db
```

### Resetting the database

1. Stop the Django server (Ctrl+C)
2. `dropdb -U hiba student_council_db`
3. `createdb -U hiba student_council_db`
4. `python manage.py migrate`
5. `python manage.py createsuperuser`
6. Restart the server

## Troubleshooting

**Port 8000 already in use**

```bash
lsof -i :8000
kill -9 <PID>
```

Alternatively, run on a different port: `python manage.py runserver 8001`.

**Import errors on startup**

Confirm the virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Static files not loading**

Rebuild Tailwind CSS and confirm the output file exists:

```bash
cd frontend
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
ls -la frontend/static/dist/output.css
```

**PostgreSQL connection refused**

```bash
brew services list
brew services start postgresql     # macOS
sudo systemctl start postgresql    # Linux
psql -U hiba -d student_council_db -c "SELECT 1;"
```

If the database does not exist, create it and confirm:

```bash
createdb student_council_db
psql -U hiba -l | grep student_council_db
```

**Celery tasks not processing**

Confirm Redis is running:

```bash
redis-cli ping
redis-server
```

Inspect task status:

```bash
celery -A student_council inspect registered
celery -A student_council inspect active
celery -A student_council purge
```

**Emails not sending**

Verify `EMAIL_HOST`, `EMAIL_PORT`, and `EMAIL_HOST_USER` in `.env` match your provider's configuration. Test directly:

```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test Body', 'from@example.com', ['to@example.com'])
```

If email delivery fails without a clear error in the Celery logs, switch to the console email backend to print outgoing emails to the terminal instead of attempting delivery:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Command Reference

**Django**

```bash
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py showmigrations
python manage.py createsuperuser
python manage.py shell
python manage.py test
python manage.py check
```

**Celery**

```bash
celery -A student_council worker --loglevel=info
celery -A student_council beat --loglevel=info
celery -A student_council inspect active
celery -A student_council inspect registered
celery -A student_council purge
```

**PostgreSQL**

```bash
psql -U hiba -d student_council_db
psql -U hiba -l
psql -U hiba -d student_council_db -c "\dt"
pg_dump -U hiba student_council_db > backup.sql
psql -U hiba student_council_db < backup.sql
```

**Redis**

```bash
redis-server
redis-cli
ping
keys *
flushall
monitor
```

## Project Structure

```
student-council/
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   ├── venv/
│   ├── student_council/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── wsgi.py
│   ├── accounts/
│   ├── clubs/
│   ├── duty_roster/
│   ├── announcements/
│   ├── competitions/
│   ├── meetings/
│   ├── discipline/
│   ├── notifications/
│   └── media/
│
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── public_base.html
│   │   ├── dashboard.html
│   │   └── ...
│   ├── static/
│   │   ├── dist/output.css
│   │   ├── src/input.css
│   │   └── js/
│   ├── package.json
│   └── tailwind.config.js
│
└── docs/
    └── LOCAL_DEVELOPMENT.md
```

## Development Tips

Test model behavior directly in the Django shell before implementing a full endpoint:

```bash
python manage.py shell

from clubs.models import Club
clubs = Club.objects.all()
print(clubs)
club = Club.objects.first()
print(club.name)
exit()
```

Inspect generated SQL for a queryset:

```python
from django.db import connection
from django.conf import settings

settings.DEBUG = True

from clubs.models import Club
Club.objects.all()

for query in connection.queries:
    print(query['sql'])
```

Monitor Celery events in real time:

```bash
celery -A student_council events
```

## Getting Help

Check logs first: the Django terminal, the Celery worker terminal, and for PostgreSQL, `journalctl -u postgresql -n 20`.

Common resolutions include restarting all four services, verifying `.env` configuration, running `python manage.py migrate`, clearing the cache (`from django.core.cache import cache; cache.clear()` via the shell), or reinstalling dependencies with `pip install -r requirements.txt --force-reinstall`.

## Next Steps

1. Review `SYSTEM_DOCUMENTATION.md` for architecture and codebase structure
2. Review `PRODUCTION_DOCUMENTATION.md` before deploying
3. Test all API endpoints
4. Complete a small end-to-end change to confirm the workflow
5. Run the test suite: `python manage.py test`

---

**Last Updated:** July 2026