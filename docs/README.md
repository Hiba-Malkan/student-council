# Student Council Management System

This is a web application for managing student council operations. It handles clubs, competitions, meetings, duty rosters, announcements, and discipline tracking. The system provides a responsive dashboard for council administrators and public pages showing available clubs to all students. **Security-first design prevents unauthorized access to restricted features** through both frontend permission checks and backend API validation.

## Features

The application handles clubs with creation, updates, deletion, and status tracking. Students discover clubs on a public page without needing to log in first. The duty roster system cycles maintenance assignments each month and alerts administrators when tasks are overdue.

Announcements reach specific roles or the entire council. Competitions track who's signed up, manage team assignments, and enforce deadlines. You can remove participants directly from signup pages with a confirmation modal that works in light and dark mode. Meetings get scheduled with attendees and automatic reminder emails. Discipline records log policy violations with severity and action tracking. Email notifications go out on a schedule (7 AM and 4 PM) and also trigger immediately when events happen.

### Security & Access Control

The system uses **permission-based role management** to control access:
- **Normal Students**: Can view announcements, sign up for clubs/competitions, and access gate pass
- **Council Members**: Can view dashboard, schedule meetings, manage duty rosters, and view discipline records
- **Administrators**: Have full access to all features and can manage everything

**Authorization Protection**:
- Direct URL access is blocked for unauthorized users with automatic redirects
- Frontend permission checks provide immediate feedback with error messages
- Backend API endpoints enforce permissions on every request
- Light mode is the default on login for a fresh user experience

### Role-Based Access Control

The system uses customizable roles with granular permission fields:
- `is_normal_student` — Restricts access to restricted features
- `can_edit_duty_roster` — Allows duty roster management
- `can_schedule_meetings` — Allows meeting creation
- `can_record_discipline` — Allows discipline record management
- `can_manage_announcements` — Allows announcement creation
- `can_manage_competitions` — Allows competition management
- `can_add_clubs` — Allows club creation
- Additional role-specific permissions for fine-grained control

Authentication uses JWT tokens so sessions are stateless. The interface is responsive and includes dark mode for students accessing it on mobile.

## Tech Stack

The backend uses Django 4.2.29 with Django REST Framework 3.15.2 delivering 20+ API endpoints. PostgreSQL 12+ serves as the database with 42 optimized tables. Redis 5.0+ handles message brokering while Celery 5.3.6 processes background tasks via Celery Beat 2.5.0 scheduler. The frontend is HTML5 with Tailwind CSS 3+ for responsive design and vanilla JavaScript ES6+ for interactivity.

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

All documentation is in the `docs/` folder.

For local development setup, see `LOCAL_DEVELOPMENT.md` which covers system requirements, installation steps, running services, development workflow, API testing, and troubleshooting.

For technical architecture details, see `SYSTEM_DOCUMENTATION.md` which explains the system design, technology stack, codebase structure, module documentation, database schema, API reference, maintenance procedures, and monitoring setup.

For production deployment, see `PRODUCTION_DOCUMENTATION.md` which covers server setup, application deployment, security hardening, backup and recovery, monitoring, and scaling strategies.

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

# Signup Management (admin only)
GET /api/competitions/{id}/signups/          # List signups for a competition
GET /api/clubs/{id}/signups/                 # List signups for a club
DELETE /api/competitions/{id}/delete_signup/ # Remove signup from competition
DELETE /api/clubs/{id}/delete_signup/        # Remove signup from club

# Admin operations
POST /api/clubs/                # Create club
PUT /api/clubs/{id}/            # Update club
DELETE /api/clubs/{id}/         # Delete club
```

To test the API, first log in to get a JWT token:

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

Backend changes to models, views, or serializers reload automatically. Refresh your browser to see them.

When you modify database models, generate and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Run tests with:

```bash
python manage.py test
```

Write Python code following PEP 8. Write JavaScript as ES6+. Use Tailwind best practices for CSS. Comments should explain why code exists, not what it does.

Modals in the signup pages use a hybrid styling approach: inline styles for base properties (padding, font size, borders) combined with Tailwind dark: prefix classes for dark mode variants. This ensures styling works reliably in both light and dark modes. If you add new modals, follow this pattern rather than relying on Tailwind classes alone.

## Deployment Checklist

Before deploying to production, complete these tasks:

- Read PRODUCTION_DOCUMENTATION.md
- Set up an Ubuntu 20.04+ server
- Configure PostgreSQL with daily backups
- Install and configure Redis
- Set up Gunicorn and Nginx
- Obtain and install SSL certificates
- Configure environment variables
- Run database migrations
- Test all services thoroughly

You can host this application on AWS, DigitalOcean, Heroku, or Linode. Each platform has different configuration requirements covered in PRODUCTION_DOCUMENTATION.md.

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

Python packages include Django 4.2.29, Django REST Framework 3.15.2, djangorestframework-simplejwt 5.5.1, Celery 5.3.6, Celery Beat 2.5.0, Redis 5.0.1, django-cors-headers 4.3.1, Pillow 12.1.1, psycopg 3.1.18 for PostgreSQL connection, python-decouple 3.8 for environment variables, and django-filter 24.1 for query filtering. See `backend/requirements.txt` for the complete list.

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

This project uses a source-available license. See `LICENSE.md` for full terms. You may view and fork this repository for study purposes, but may not use, deploy, or incorporate this code without explicit written permission. AI/ML training on this code is prohibited. Contact hiba.malkan@gmail.com for permission requests.

## Support

Documentation lives in the `docs/` folder. Open an issue on GitHub to report bugs. Email hiba.malkan@gmail.com for questions or emergencies.

Contact hiba.malkan@gmail.com for support, questions, or incident reports.

## Status

The backend is production ready, the frontend is production ready, the database uses PostgreSQL with 42 tables, the API has 20+ tested endpoints, documentation is complete, security is hardened, and performance is optimized.

## Quick Links

- [Local Development Guide](./LOCAL_DEVELOPMENT.md)
- [Production Deployment Guide](./PRODUCTION_DOCUMENTATION.md)
- [System Architecture Documentation](./SYSTEM_DOCUMENTATION.md)
- [License](./LICENSE.md)
- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

The application is built with Django and Django REST Framework, styled with Tailwind CSS, uses Celery for background processing, and PostgreSQL for data storage.

**Written by Hiba**

Last Updated: March 26, 2026  
Version: 1.0  
Status: Production Ready
