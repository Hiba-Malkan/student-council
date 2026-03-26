# Student Council Management System — Local Development Guide

Set up and run the application locally on your machine in under 20 minutes.

## Quick Start

Clone the repository, create a Python virtual environment, install dependencies, set up the database, and start four service terminals:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your configuration

createdb student_council_db
python manage.py migrate
python manage.py createsuperuser
```

Open four terminals and run these commands simultaneously:

```bash
# Terminal 1
cd backend && source venv/bin/activate && python manage.py runserver

# Terminal 2
cd backend && source venv/bin/activate && celery -A student_council worker --loglevel=info

# Terminal 3
cd backend && source venv/bin/activate && celery -A student_council beat --loglevel=info

# Terminal 4
redis-server
```

Visit http://localhost:8000 to access the application.

## System Requirements

You need:

- macOS, Linux, or Windows with WSL2
- Python 3.13 or later
- Node.js 18 or later
- PostgreSQL 12 or later
- Redis latest stable version
- Git latest version

Verify your installations:

```bash
python3 --version
node --version
psql --version
redis-cli --version
git --version
```

Hardware should have at least 4GB RAM, a dual-core processor at 2GHz, and 5GB free disk space with a stable internet connection.

## Installation

Clone the repository and navigate into the directory:

```bash
git clone https://github.com/Hiba-Malkan/student-council.git
cd student-council
```

Create a Python virtual environment and activate it:

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

On Windows, use `venv\Scripts\activate` instead.

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Create the `.env` file by copying the example:

```bash
cp .env.example .env
```

Edit `backend/.env` with your configuration:

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

Set up the database:

```bash
createdb student_council_db
python manage.py migrate
python manage.py createsuperuser
```

Verify the database has all 42 tables:

```bash
psql -U hiba -d student_council_db -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';"
```

Install frontend dependencies and build Tailwind CSS:

```bash
cd ../frontend
npm install
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

Watch for changes automatically:

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch
```

## Running Services

The 4-terminal approach is recommended for development. Each terminal shows logs from one service, making it easy to debug issues.

**Terminal 1 — Django Development Server:**

```bash
cd backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

The server runs on http://localhost:8000 and auto-reloads whenever you change Python code. Request logs appear in real-time so you can see what the application is doing.

**Terminal 2 — Celery Worker:**

```bash
cd backend
source venv/bin/activate
celery -A student_council worker --loglevel=info
```

The worker processes background tasks asynchronously, such as sending email notifications. Task execution logs appear here so you can see if notifications are being sent correctly.

**Terminal 3 — Celery Beat:**

```bash
cd backend
source venv/bin/activate
celery -A student_council beat --loglevel=info
```

Beat runs scheduled tasks automatically. Notifications are sent at 7 AM and 4 PM each day. Scheduling logs appear in this terminal.

**Terminal 4 — Redis:**

```bash
redis-server
```

Redis acts as the message broker between Django and Celery. Connection logs appear here.

Watch out — if you close a terminal, that service stops. The application continues running but features depending on that service will fail. For example, if you close the Celery terminal, background emails will not send even though Django keeps running.

Alternatively, create a bash script `start_dev.sh` to run all services:

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

Run it with `bash start_dev.sh`. However, logs mix together, making it harder to debug.

## Development Workflow

### Editing Templates and Styles

Edit HTML templates in `frontend/templates/`. Django reloads templates automatically, so refresh your browser to see changes immediately without restarting the server.

Edit CSS in `frontend/static/src/input.css`. Rebuild the compiled CSS with Tailwind:

```bash
cd frontend
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

Use the watch flag to rebuild automatically whenever the CSS changes:

```bash
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css --watch
```

### Editing Python Code

When you modify models, views, or serializers in the backend, Django detects the changes and auto-reloads. Refresh your browser and the new code runs immediately. No server restart needed.

### Adding Database Columns

When you modify a model in `models.py`, generate a migration:

```bash
python manage.py makemigrations
```

Review the generated migration file before applying it:

```bash
cat backend/accounts/migrations/000X_*.py
```

Apply the migration to update the database schema:

```bash
python manage.py migrate
```

Verify the changes applied:

```bash
python manage.py showmigrations
```

### Adding a New Field to a Model

Example: Add a description field to the Club model.

Edit `backend/clubs/models.py`:

```python
class Club(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    # Add the new field:
    location = models.CharField(max_length=200, default='')
```

Generate a migration:

```bash
python manage.py makemigrations clubs
```

Apply the migration:

```bash
python manage.py migrate
```

Update the serializer in `backend/clubs/serializers.py` to include the new field:

```python
class ClubSerializer(serializers.ModelSerializer):
    class Meta:
        model = Club
        fields = ['id', 'name', 'description', 'location']
```

Test via the API:

```bash
curl http://localhost:8000/api/clubs/
```

## API Testing

Test the API with `curl` commands to verify endpoints work correctly.

Get all active clubs:

```bash
curl http://localhost:8000/api/clubs/
```

Filter clubs by status:

```bash
curl "http://localhost:8000/api/clubs/?status=active"
```

Search clubs by name:

```bash
curl "http://localhost:8000/api/clubs/?search=coding"
```

Paginate through results:

```bash
curl "http://localhost:8000/api/clubs/?page=2"
```

Login to get a JWT token:

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"your_username","password":"your_password"}'
```

The response contains access and refresh tokens. Use the access token for protected endpoints:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/accounts/me/
```

### Using REST Client Extension

Install the REST Client extension in VS Code. Create a `test.http` file:

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

Click "Send Request" above each endpoint to execute it. Responses appear in a side panel.

### Using Postman

Download Postman and create a collection called "Student Council". Add requests for each endpoint. Use the Authorization tab to set Bearer tokens. Save responses to your collection for reference.

## Database Management

View all database tables:

```bash
psql -U hiba -d student_council_db -c "\dt"
```

View the structure of a specific table:

```bash
psql -U hiba -d student_council_db -c "\d clubs_club"
```

Run a SQL query:

```bash
psql -U hiba -d student_council_db -c "SELECT * FROM accounts_user;"
```

Access the PostgreSQL interactive shell:

```bash
psql -U hiba -d student_council_db
```

Inside the shell:

```
\dt                   # List tables
\d clubs_club         # Describe table structure
SELECT * FROM clubs_club;  # Run query
\q                    # Exit shell
```

Backup the database to a file:

```bash
pg_dump -U hiba student_council_db > backup.sql
```

Compress the backup:

```bash
pg_dump -U hiba student_council_db | gzip > backup.sql.gz
```

Restore from a backup:

```bash
psql -U hiba student_council_db < backup.sql
```

Restore from a compressed backup:

```bash
gunzip -c backup.sql.gz | psql -U hiba student_council_db
```

### Reset Database

Start fresh by dropping and recreating the database:

1. Stop the Django server by pressing Ctrl+C

2. Drop the existing database:

```bash
dropdb -U hiba student_council_db
```

3. Create a fresh database:

```bash
createdb -U hiba student_council_db
```

4. Run migrations:

```bash
python manage.py migrate
```

5. Create a new superuser:

```bash
python manage.py createsuperuser
```

6. Restart the Django server

## Troubleshooting

If port 8000 is already in use by another process, find and stop it:

```bash
lsof -i :8000
kill -9 <PID>
```

Alternatively, run Django on a different port:

```bash
python manage.py runserver 8001
```

If you see an import error when running Django, ensure the virtual environment is activated:

```bash
source venv/bin/activate
```

Reinstall dependencies to resolve missing modules:

```bash
pip install -r requirements.txt
```

If static CSS files are not loading (page looks unstyled), rebuild the Tailwind CSS:

```bash
cd frontend
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

Verify the CSS file exists:

```bash
ls -la frontend/static/dist/output.css
```

If PostgreSQL refuses connections, verify it's running:

```bash
brew services list
```

On macOS, start PostgreSQL:

```bash
brew services start postgresql
```

On Linux:

```bash
sudo systemctl start postgresql
```

Test the connection:

```bash
psql -U hiba -d student_council_db -c "SELECT 1;"
```

If the database doesn't exist, create it:

```bash
createdb student_council_db
```

Verify it was created:

```bash
psql -U hiba -l | grep student_council_db
```

If Celery tasks are not processing, verify Redis is running:

```bash
redis-cli ping
```

If Redis doesn't respond with PONG, start it:

```bash
redis-server
```

Check what tasks are registered with Celery:

```bash
celery -A student_council inspect registered
```

View active tasks:

```bash
celery -A student_council inspect active
```

If tasks are stuck, clear the queue:

```bash
celery -A student_council purge
```

If email notifications are not sending, check the email configuration in `.env`. Verify EMAIL_HOST, EMAIL_PORT, and EMAIL_HOST_USER match your email provider.

Test email sending in the Django shell:

```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test Body', 'from@example.com', ['to@example.com'])
```

Check Celery logs for errors. If the logs don't show a clear error, enable console email backend in `settings.py` so emails print to the terminal:

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Useful Commands

Django commands for development:

```bash
python manage.py runserver          # Start development server
python manage.py makemigrations     # Create migrations
python manage.py migrate            # Apply migrations
python manage.py showmigrations     # Show migration status
python manage.py createsuperuser    # Create admin account
python manage.py shell              # Enter Python REPL
python manage.py test               # Run tests
python manage.py check              # Check for errors
```

Celery commands for background tasks:

```bash
celery -A student_council worker --loglevel=info  # Start worker
celery -A student_council beat --loglevel=info    # Start scheduler
celery -A student_council inspect active          # View active tasks
celery -A student_council inspect registered      # View all tasks
celery -A student_council purge                   # Clear task queue
```

PostgreSQL commands for database management:

```bash
psql -U hiba -d student_council_db        # Access database
psql -U hiba -l                           # List all databases
psql -U hiba -d student_council_db -c "\dt"  # List tables
pg_dump -U hiba student_council_db > backup.sql  # Backup database
psql -U hiba student_council_db < backup.sql   # Restore database
```

Redis commands for message broker:

```bash
redis-server        # Start Redis
redis-cli           # Access Redis CLI
ping                # Check connection (in redis-cli)
keys *              # View all keys
flushall            # Delete all keys
monitor             # Monitor real-time commands
```

## Project Structure

```
student-council/
├── backend/                    Django application
│   ├── manage.py              CLI tool
│   ├── requirements.txt        Python dependencies
│   ├── .env                    Configuration (create this)
│   ├── venv/                   Virtual environment (auto-created)
│   ├── student_council/        Main project package
│   │   ├── settings.py        Django configuration
│   │   ├── urls.py            URL routing
│   │   ├── celery.py          Celery setup
│   │   └── wsgi.py            WSGI entry point
│   ├── accounts/              User authentication
│   ├── clubs/                 Club management
│   ├── duty_roster/           Duty assignments
│   ├── announcements/         Announcements
│   ├── competitions/          Competitions
│   ├── meetings/              Meetings
│   ├── discipline/            Discipline records
│   ├── notifications/         Email notifications
│   ├── media/                 Uploaded files directory
│   └── db.sqlite3             SQLite backup (local only)
│
├── frontend/                  Static assets and templates
│   ├── templates/             HTML templates
│   │   ├── base.html         Main template with navigation
│   │   ├── public_base.html  Public pages template
│   │   ├── dashboard.html    Admin dashboard
│   │   └── ...               Other page templates
│   ├── static/               Static assets
│   │   ├── dist/output.css   Compiled Tailwind (auto-generated)
│   │   ├── src/input.css     Tailwind source (edit this)
│   │   └── js/               JavaScript files
│   ├── package.json          npm dependencies
│   └── tailwind.config.js    Tailwind configuration
│
└── docs/                      Documentation
    └── LOCAL_DEVELOPMENT.md   This file
```

## Development Tips

Test code changes in the Django shell:

```bash
python manage.py shell

from clubs.models import Club
clubs = Club.objects.all()
print(clubs)
club = Club.objects.first()
print(club.name)
exit()
```

Enable query logging to see SQL statements:

```bash
from django.db import connection
from django.conf import settings

settings.DEBUG = True

from clubs.models import Club
Club.objects.all()

for query in connection.queries:
    print(query['sql'])
```

Debug code with print statements. Output appears in the Django terminal:

```python
print("DEBUG: variable =", variable)
```

Monitor active Celery tasks in real-time:

```bash
celery -A student_council events
```

Test email sending locally:

```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Body', 'from@example.com', ['to@example.com'])
```

The email prints to the console if EMAIL_BACKEND is set to console in settings.

## Getting Help

Always check logs first when something breaks. Django logs appear in the terminal where the server runs. Celery logs appear in the Celery worker terminal. PostgreSQL logs can be viewed with `journalctl -u postgresql -n 20`.

Common fixes include restarting all services (usually resolves temporary issues), checking the `.env` file (verify all settings are correct), running migrations (`python manage.py migrate`), clearing cache (`python manage.py shell` → `from django.core.cache import cache` → `cache.clear()`), and reinstalling dependencies (`pip install -r requirements.txt --force-reinstall`).

## Next Steps

Once local development is running smoothly:

1. Read SYSTEM_DOCUMENTATION.md to understand the codebase structure
2. Read PRODUCTION_DOCUMENTATION.md to learn about deployment
3. Test all API endpoints to verify they work correctly
4. Make a small change to practice the development workflow
5. Run the test suite with `python manage.py test`

---

**Document Version:** 1.0  
**Last Updated:** March 26, 2026  
**Status:** Ready for Local Development