# Student Council Management System

This is a web application for managing student council operations. It handles clubs, competitions, meetings, duty rosters, announcements, and discipline tracking. The system provides a responsive dashboard for council administrators and public pages showing available clubs to all students without login required.

## Features

The application supports clubs management with creation, updates, deletion, and status tracking. A public endpoint lists active clubs so students can discover organizations without authentication. The duty roster system automatically cycles maintenance duties to students each month and alerts administrators to overdue tasks.

Announcements go to specific roles or the entire student council. Competition management tracks participants and enforces deadlines. Meetings can be scheduled with attendees and reminder emails sent automatically. Discipline records document policy violations with severity levels and action tracking. Notifications are sent via email on a schedule (7 AM and 4 PM) and triggered by events.

The system uses five customizable roles to control what users can do. Authentication via JWT tokens keeps sessions stateless. The dashboard is responsive and includes dark mode support for students accessing the system on mobile devices.

## Tech Stack

The backend uses Django 4.2.7 with Django REST Framework delivering 20+ API endpoints. PostgreSQL 12+ serves as the database with 42 optimized tables. Redis handles message brokering while Celery processes background tasks via a Beat scheduler. The frontend is HTML5 with Tailwind CSS 3+ for responsive design and vanilla JavaScript ES6+ for interactivity.

Gunicorn serves the application in production behind Nginx as a reverse proxy handling HTTPS/SSL termination. Git manages version control. The application runs on macOS, Linux, or Windows with WSL2. Let's Encrypt provides free SSL certificates for HTTPS.

## Getting Started

You need Python 3.13+, Node.js 18+, PostgreSQL 12+, Redis, and Git installed before beginning.

Clone the repository and enter the directory:

```bash
git clone https://github.com/Hiba-Malkan/student-council.git
cd student-council
```

Set up the backend by creating a virtual environment, installing dependencies, and configuring the database:

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

cd ../frontend
npm install
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

Open four terminals to run all services:

Terminal 1 starts the Django development server:

```bash
cd backend
source venv/bin/activate
python manage.py runserver
```

Terminal 2 runs the Celery worker for background tasks:

```bash
cd backend
source venv/bin/activate
celery -A student_council worker --loglevel=info
```

Terminal 3 runs Celery Beat for scheduled tasks:

```bash
cd backend
source venv/bin/activate
celery -A student_council beat --loglevel=info
```

Terminal 4 runs Redis for message brokering:

```bash
redis-server
```

Visit http://localhost:8000 in your browser to access the application.

## Project Structure

```
student-council/
├── backend/                    # Django application
│   ├── manage.py               # Django CLI
│   ├── requirements.txt         # Python dependencies
│   ├── .env                    # Configuration (create this)
│   ├── student_council/        # Main project settings
│   ├── accounts/               # User authentication
│   ├── clubs/                  # Clubs management
│   ├── duty_roster/            # Duty assignments
│   ├── announcements/          # Announcements
│   ├── competitions/           # Competitions
│   ├── meetings/               # Meetings
│   ├── discipline/             # Discipline records
│   ├── notifications/          # Email notifications
│   ├── media/                  # Uploaded files
│   └── venv/                   # Virtual environment
│
├── frontend/                   # Static assets & templates
│   ├── templates/              # HTML templates
│   ├── static/                 # CSS, JS, images
│   ├── package.json            # Node dependencies
│   └── tailwind.config.js      # Tailwind configuration
│
├── docs/                       # Documentation
│   ├── LOCAL_DEVELOPMENT.md    # Development setup
│   ├── PRODUCTION_DOCUMENTATION.md
│   ├── SYSTEM_DOCUMENTATION.md
│   └── README.md               # This file
│
└── .gitignore                  # Git ignore rules
```

## Documentation

For local development setup, see `docs/LOCAL_DEVELOPMENT.md` which covers system requirements, installation steps, running services, development workflow, API testing, and troubleshooting.

For technical architecture details, see `docs/SYSTEM_DOCUMENTATION.md` which explains the system design, technology stack, codebase structure, module documentation, database schema, API reference, maintenance procedures, and monitoring setup.

For production deployment, see `docs/PRODUCTION_DOCUMENTATION.md` which covers server setup, application deployment, security hardening, backup and recovery, monitoring, and scaling strategies.

## API Endpoints

Public endpoints require no authentication:

```bash
GET /api/clubs/                 # List all active clubs
GET /api/clubs/?status=active   # Filter clubs by status
GET /api/clubs/?search=name     # Search clubs by name
GET /public/clubs/              # Public clubs page
```

Protected endpoints require a valid JWT token:

```bash
POST /api/accounts/login/       # Login and receive token
GET /api/accounts/me/           # Current user's profile
GET /api/duty-roster/           # User's assigned duties
GET /api/announcements/         # All announcements
POST /api/clubs/                # Create club (admin only)
PUT /api/clubs/{id}/            # Update club (admin only)
DELETE /api/clubs/{id}/         # Delete club (admin only)
```

To test the API, first log in to receive a JWT token:

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

The response contains access and refresh tokens. Use the access token for subsequent requests:

```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://localhost:8000/api/accounts/me/
```



## Development

Frontend changes require rebuilding Tailwind CSS. Edit templates in `frontend/templates/` or styles in `frontend/static/`, then run:

```bash
cd frontend
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

Backend changes to models, views, or serializers take effect immediately because Django reloads on file changes. Refresh your browser to see the updates.

When you modify database models, create and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Run the test suite with:

```bash
python manage.py test
```

Write code following PEP 8 for Python, ES6+ for JavaScript, and Tailwind best practices for CSS. Keep comments explaining why code exists, not what it does.

## Deployment Checklist

Before deploying to production, complete these tasks:

- Read `docs/PRODUCTION_DOCUMENTATION.md`
- Set up an Ubuntu 20.04+ server
- Configure PostgreSQL with daily backups
- Install and configure Redis
- Set up Gunicorn and Nginx
- Obtain and install SSL certificates
- Configure environment variables
- Run database migrations
- Test all services thoroughly

You can host this application on AWS, DigitalOcean, Heroku, or Linode. Each platform has different configuration requirements covered in `docs/PRODUCTION_DOCUMENTATION.md`.

The `.env` file must never be committed to version control. Copy `.env.example` to `.env` and fill in your values:

```env
SECRET_KEY=your-super-secret-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_council_db
DB_USER=appuser
DB_PASSWORD=strong_password
DB_HOST=localhost
DB_PORT=5432

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

EMAIL_HOST=smtp.sendgrid.net
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_key
```

## Dependencies

Python packages include Django 4.2.7, Django REST Framework, Celery, Redis, psycopg2 for PostgreSQL connection, and python-decouple for environment variables. See `backend/requirements.txt` for the complete list.

System dependencies are PostgreSQL 12+, Redis 6+, Python 3.13+, and Node.js 18+.

## Security

The system implements JWT token-based authentication with role-based access control. CSRF protection prevents cross-site request forgery. SQL injection attacks are prevented through Django's ORM. XSS protection is built into template rendering. Passwords are hashed using Django's secure algorithms. HTTPS/SSL is supported for encrypted connections. Sensitive configuration lives in environment variables, never hardcoded. All user inputs are validated.

Always use HTTPS in production. Keep SECRET_KEY secret and rotate it periodically. Use strong database passwords with uppercase, lowercase, numbers, and symbols. Keep Python and system packages updated with security patches. Monitor logs for suspicious activity. Enable and test database backups regularly. Configure firewalls to restrict access. Conduct periodic security audits.

## Database

The system uses 42 PostgreSQL tables for storage including accounts_user, accounts_role, accounts_userrole for user management; clubs_club, clubs_clubmember for organizations; duty_roster_duty for assignments; announcements_announcement for posts; competitions_competition for events; meetings_meeting for schedules; discipline_record for violations; and notifications_notification for emails.

Backup the database regularly:

```bash
pg_dump -U username student_council_db > backup.sql
```

Restore from backup:

```bash
psql -U username student_council_db < backup.sql
```

## Performance

The application uses database indexes on frequently queried fields for faster lookups. Redis caches repeated queries to reduce database load. Celery processes background tasks asynchronously so HTTP requests complete quickly. Django's select_related() method reduces database queries. Static files are compressed. Frontend features lazy loading. Connection pooling reuses database connections.

Monitor these metrics: response time should stay under 200ms, error rate below 1%, database connections under 80, memory below 80%, CPU below 70%, and Celery queue length below 100 items.

## Troubleshooting

If port 8000 is in use, find and kill the process:

```bash
lsof -i :8000
kill -9 <PID>
```

If the database refuses connections, start PostgreSQL:

```bash
brew services start postgresql
```

On Linux use `sudo systemctl start postgresql`.

If Redis is not running, start it:

```bash
redis-server
```

If static files don't load, collect them:

```bash
python manage.py collectstatic
```

See `docs/LOCAL_DEVELOPMENT.md` for additional troubleshooting guidance.

## License

This project uses a source-available license. See `docs/LICENSE.md` for full terms. You may view and fork this repository for study purposes, but may not use, deploy, or incorporate this code without explicit written permission. AI/ML training on this code is prohibited. Contact hiba.malkan@gmail.com for permission requests.

## Support

Comprehensive documentation lives in the `docs/` folder and should be reviewed carefully before requesting assistance. Most setup, usage, and troubleshooting issues are resolved at this step. If followed properly, you will not need to escalate 99% of the time (¬_¬).

For bug reports, open an issue on GitHub. For questions, emergencies, or other inquiries, email hiba.malkan@gmail.com. Support is provided on a selective, best-effort basis. Clear, detailed, and well-prepared requests receive priority. Extra effort or creative persuasion is always appreciated <3.

Requests that skip steps or ignore the documentation may not receive a response.

## Status

The backend is production ready, the frontend is production ready, the database uses PostgreSQL with 42 tables, the API has 20+ tested endpoints, documentation is complete, security is hardened, and performance is optimized.

## Quick Links

- [Local Development Guide](./docs/LOCAL_DEVELOPMENT.md)
- [Production Deployment Guide](./docs/PRODUCTION_DOCUMENTATION.md)
- [System Architecture Documentation](./docs/SYSTEM_DOCUMENTATION.md)
- [License](./docs/LICENSE.md)
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

The application is built with Django and Django REST Framework, styled with Tailwind CSS, uses Celery for background processing, and PostgreSQL for data storage.

**Written by Hiba**

Last Updated: March 26, 2026  
Version: 1.0
