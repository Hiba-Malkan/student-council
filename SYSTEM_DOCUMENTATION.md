# Student Council Management System
## Technical Documentation

**Version:** 1.0  
**Date:** March 26, 2026  
**Organization:** Student Council  
**Status:** Production Ready

---

This is an enterprise-grade web application built with Django REST Framework and PostgreSQL. It provides complete management capabilities for student organizations, including clubs, competitions, meetings, duty rosters, announcements, and discipline tracking.

The system centralizes student council operations, improves communication between council and students, automates routine administrative tasks, maintains organized records of all council activities, and provides transparent public information about club listings.

The architecture uses an API-first approach with 20+ RESTful endpoints, PostgreSQL with 42 optimized tables, Celery with Redis for asynchronous processing, and a responsive Tailwind CSS frontend with JWT authentication and role-based access control.

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Codebase Structure](#codebase-structure)
3. [Module Documentation](#module-documentation)
4. [Data Models](#data-models)
5. [API Reference](#api-reference)
6. [Deployment Architecture](#deployment-architecture)
7. [Maintenance Procedures](#maintenance-procedures)
8. [Monitoring & Logging](#monitoring--logging)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Web Browser (HTML, CSS, JavaScript, Tailwind CSS)       │   │
│  │  • Dashboard                                             │   │
│  │  • Admin Panel                                           │   │
│  │  • Public Pages                                          |   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────┬──────────────────────────────────────────-┘
                      │ HTTP/HTTPS
┌─────────────────────▼──────────────────────────────────────────--
│                    API Layer                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Django REST Framework                                   │   │
│  │  • REST Endpoints (/api/*)                               │   │
│  │  • JWT Authentication                                    │   │
│  │  • Serializers & Validation                              │   │
│  │  • Permission Classes                                    │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────┬──────────────────────────────────────┬────────────────┘
          │                                      │
          │ SQL                                  │ Tasks
┌─────────▼──────────────────┐  ┌──────────────▼──────────────┐
│   PostgreSQL Database      │  │  Message Queue System       │
│  ┌───────────────────────┐ │  │  ┌────────────────────────┐ │
│  │ • 42 Tables           │ │  │  │  Redis (Message Broker)│ │
│  │ • Users & Roles       │ │  │  │  Celery (Task Queue)   │ │
│  │ • Clubs & Members     │ │  │  │  Celery Beat (Scheduler) │
│  │ • Duties & Tasks      │ │  │  └────────────────────────┘ │
│  │ • Announcements       │ │  │                             │
│  │ • Competitions        │ │  │  Background Jobs:           │
│  │ • Meetings            │ │  │  • Email Notifications      |
│  │ • Discipline Records  │ │  │  • Duty Cycling             │
│  │ • Notifications       │ │  │  • Scheduled Tasks          │
│  └───────────────────────┘ │  │                             │
└────────────────────────────┘  └─────────────────────────────┘
```

The frontend runs on HTML5 with CSS3 for structure and styling, using Tailwind CSS 3+ for responsive design and vanilla JavaScript ES6+ for interactivity. The backend is built with Django 4.2.7 and Django REST Framework to deliver the API. PostgreSQL 12+ serves as the primary data store with 42 optimized tables. Redis handles message brokering while Celery manages background tasks with a scheduler via Celery Beat. Authentication relies on JWT tokens for stateless request validation. Gunicorn serves the Django application in production, and Nginx acts as a reverse proxy handling HTTPS/SSL termination and static file serving.

---

## Codebase Structure

### Directory Organization

```
student-council/
│
├── backend/                          # Django Project Root
│   ├── manage.py                     # Django CLI tool
│   ├── requirements.txt              # Python dependencies
│   ├── .env                          # Environment variables
│   ├── db.sqlite3                    # SQLite backup (dev)
│   │
│   ├── student_council/              # Main Project Package
│   │   ├── __init__.py
│   │   ├── settings.py              # Django configuration
│   │   ├── urls.py                  # URL routing
│   │   ├── wsgi.py                  # WSGI config (production)
│   │   ├── celery.py                # Celery configuration
│   │   └── asgi.py                  # ASGI config (async)
│   │
│   ├── accounts/                     # Authentication & Users
│   │   ├── models.py                # User, Role models
│   │   ├── views.py                 # User API views
│   │   ├── serializers.py           # User serializers
│   │   ├── permissions.py           # Custom permissions
│   │   ├── urls.py                  # User routes
│   │   └── migrations/              # Database migrations
│   │
│   ├── clubs/                        # Clubs Management
│   │   ├── models.py                # Club model
│   │   ├── views.py                 # Club API & HTML views
│   │   ├── serializers.py           # Club serializers
│   │   ├── permissions.py           # Club permissions
│   │   ├── admin.py                 # Django admin config
│   │   ├── urls.py                  # Club routes
│   │   └── migrations/              # Database migrations
│   │
│   ├── duty_roster/                 # Duty Management
│   │   ├── models.py                # Duty model
│   │   ├── views.py                 # Duty API views
│   │   ├── serializers.py           # Duty serializers
│   │   ├── permissions.py           # Duty permissions
│   │   ├── urls.py                  # Duty routes
│   │   └── migrations/              # Database migrations
│   │
│   ├── announcements/               # Announcements
│   │   ├── models.py                # Announcement model
│   │   ├── views.py                 # Announcement API
│   │   ├── serializers.py           # Serializers
│   │   ├── urls.py                  # Routes
│   │   └── migrations/              # Migrations
│   │
│   ├── competitions/                # Competitions
│   │   ├── models.py                # Competition model
│   │   ├── views.py                 # API views
│   │   ├── serializers.py           # Serializers
│   │   ├── urls.py                  # Routes
│   │   └── migrations/              # Migrations
│   │
│   ├── meetings/                    # Meetings
│   │   ├── models.py                # Meeting model
│   │   ├── views.py                 # API views
│   │   ├── serializers.py           # Serializers
│   │   └── migrations/              # Migrations
│   │
│   ├── discipline/                  # Discipline Records
│   │   ├── models.py                # Discipline model
│   │   ├── views.py                 # API views
│   │   ├── serializers.py           # Serializers
│   │   └── migrations/              # Migrations
│   │
│   ├── notifications/               # Email Notifications
│   │   ├── models.py                # Notification model
│   │   ├── tasks.py                 # Celery tasks
│   │   ├── signals.py               # Django signals
│   │   ├── utils.py                 # Email utilities
│   │   ├── views.py                 # API views
│   │   └── migrations/              # Migrations
│   │
│   ├── media/                       # User Uploaded Files
│   │   ├── announcements/
│   │   ├── club_logos/
│   │   ├── competitions/
│   │   └── meetings/
│   │
│   └── venv/                        # Virtual Environment
│
├── frontend/                         # Frontend Assets
│   ├── templates/                   # HTML Templates
│   │   ├── base.html                # Main template (sidebar)
│   │   ├── public_base.html         # Public template
│   │   ├── login.html               # Login page
│   │   ├── dashboard.html           # Dashboard
│   │   ├── forgot_password.html     # Password reset
│   │   │
│   │   ├── clubs/                   # Club templates
│   │   │   ├── clubs.html           # Club list (admin)
│   │   │   └── public_clubs.html    # Club list (public)
│   │   │
│   │   ├── announcements/           # Announcement templates
│   │   │   ├── announcements.html
│   │   │   ├── new_announcement.html
│   │   │   └── announcement_detail.html
│   │   │
│   │   ├── duty-roster/             # Duty templates
│   │   │   └── duty_roster.html
│   │   │
│   │   ├── competitions/            # Competition templates
│   │   │   └── competitions.html
│   │   │
│   │   ├── meetings/                # Meeting templates
│   │   │   └── meetings.html
│   │   │
│   │   └── discipline/              # Discipline templates
│   │       ├── discipline.html
│   │       └── discipline_form.html
│   │
│   ├── static/                      # Static Assets
│   │   ├── dist/                    # Compiled CSS
│   │   │   └── output.css           # Tailwind compiled CSS
│   │   ├── src/                     # Source CSS
│   │   │   └── input.css            # Tailwind input
│   │   ├── css/                     # Additional CSS
│   │   ├── js/                      # Additional JS
│   │   └── images/                  # Static images
│   │
│   ├── package.json                 # npm dependencies
│   ├── tailwind.config.js           # Tailwind configuration
│   └── TAILWIND_SETUP.md            # Tailwind guide
│
├── docs/                            # Documentation Files
│   ├── COMPLETE_DOCUMENTATION.md    # Full docs (submission)
│   ├── LOCAL_DEVELOPMENT.md         # Dev setup guide
│   └── PRODUCTION_DOCUMENTATION.md  # Deployment guide
│
├── .gitignore                       # Git ignore rules
├── start_services.sh                # Service startup script
├── EMAIL_TROUBLESHOOTING.md        # Email setup guide
├── ROUTING_UPDATES.md              # Routing changes
└── POSTGRESQL_MIGRATION.md         # DB migration guide
```

---

## Module Documentation

### Accounts Module

The accounts module handles user authentication and role management. It implements JWT token-based authentication with role-based access control supporting five customizable role types. Users can log in with their credentials to receive access and refresh tokens for subsequent API requests.

The module contains the User and Role models. Users have usernames, emails, and hashed passwords. Roles define what actions users can perform in the system, such as creating clubs, managing duties, or posting announcements. The UserRole model maps users to their assigned roles.

View endpoints allow users to log in, retrieve their profile, and manage their account settings. Permission classes in `permissions.py` check whether a user has the necessary role permissions before allowing access to protected endpoints.

Database tables:
- `accounts_user` — Stores user accounts with credentials
- `accounts_role` — Defines available role types and their permissions
- `accounts_userrole` — Maps users to roles (many-to-many relationship)

### Clubs Module

The clubs module manages student organizations and their memberships. Authorized administrators can create, edit, and delete clubs. The system tracks club status (active, under review, or inactive), membership counts, and founder information.

Each club has a name, description, logo image, founding year, and current member count. The ClubMember model tracks which users belong to which clubs and what role they hold within that club (president, vice-president, or regular member).

The public API endpoint returns all active clubs without requiring authentication, allowing the frontend to display a public clubs page. Admin endpoints require authentication and appropriate permissions to modify club data.

Database tables:
- `clubs_club` — Stores club information including status and metadata
- `clubs_clubmember` — Tracks club membership and member roles

### Duty Roster Module

The duty roster system assigns maintenance duties to students on a rotating basis. Each student receives a duty type (such as green field maintenance or break area cleaning) along with a due date. The system tracks whether the duty is pending, completed, or overdue.

Duties are assigned at the start of each month and can be marked complete when the student finishes the work. An automated monthly job cycles duties to new students. The system flags overdue duties to alert administrators that a student has not completed their assigned task.

Database tables:
- `duty_roster_duty` — Stores individual duty assignments with status and dates

### Announcements Module

The announcements module allows administrators to post news and information to the student council. Each announcement has a title, content, and publication date. Announcements can target specific roles (such as club presidents) or reach all users. The system stores the author ID and publication status so admins can draft and publish announcements at desired times.

Database tables:
- `announcements_announcement` — Stores announcement text and metadata

### Notifications Module

The notifications module sends email messages to users when important events occur. Celery tasks in `tasks.py` handle the actual email sending asynchronously so HTTP requests complete quickly. The system uses Django signals to trigger notifications automatically when announcements are published, duties are assigned, or meetings are scheduled.

Email templates render the HTML content with user-specific information. The notification record stores the recipient, subject, and message text along with a flag indicating whether the email was successfully sent. Scheduled tasks run twice daily (7 AM and 4 PM) to send pending notifications.

Key background tasks:
- Send announcement emails to subscribed roles
- Send daily duty reminders for overdue tasks
- Send event notifications for upcoming meetings and competitions

Database tables:
- `notifications_notification` — Stores email records and delivery status

### Competitions Module

The competitions module lets administrators create and manage student competitions. Each competition has a title, description, start and end dates, and participation requirements. The system tracks which students have entered each competition.

Database tables:
- `competitions_competition` — Stores competition information and deadlines
- `competitions_participant` — Tracks student entries for each competition

### Meetings Module

The meetings module schedules council meetings and tracks attendance. Each meeting has a date, time, location, and description. The system stores notes from the meeting and can send reminder emails before the scheduled time.

Database tables:
- `meetings_meeting` — Stores meeting schedules and details

### Discipline Module

The discipline module records instances where students violate council policies or rules. Each record includes the student name, violation description, severity level, date of incident, and any actions taken. The system maintains a history of all discipline cases for reference.

Database tables:
- `discipline_record` — Stores discipline case information and action history

## Data Models

### Core Database Schema

```
┌─────────────────────────────────────────────────────────────┐
│                      User Management                        │
├─────────────────────────────────────────────────────────────┤
│ accounts_user                                               │
│ • id (PK)                                                   │
│ • username (unique)                                         │
│ • email                                                     │
│ • password (hashed)                                         │
│ • is_active, is_staff, is_superuser                         │
│ • date_joined                                               │
│                                                             │
│ accounts_role                                               │
│ • id (PK)                                                   │
│ • name (Admin, President, etc.)                             │
│ • permissions (can_add_clubs, can_manage_duties, etc.)      │
│                                                             │
│ accounts_userrole                                           │
│ • id (PK)                                                   │
│ • user_id (FK → accounts_user)                              │
│ • role_id (FK → accounts_role)                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Clubs Management                         │
├─────────────────────────────────────────────────────────────┤
│ clubs_club                                                  │
│ • id (PK)                                                   │
│ • name                                                      │
│ • description                                               │
│ • logo                                                      │
│ • status (active, under_review, inactive)                   │
│ • established_year                                          │
│ • member_count                                              │
│ • created_by (FK → accounts_user)                           │
│ • created_at, updated_at                                    │
│                                                             │
│ clubs_clubmember                                            |
│ • id (PK)                                                   │
│ • user_id (FK → accounts_user)                              │
│ • club_id (FK → clubs_club)                                 │
│ • role (president, vice_president, member)                  │
│ • joined_date                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Duty Management                          │
├─────────────────────────────────────────────────────────────┤
│ duty_roster_duty                                            │
│ • id (PK)                                                   │
│ • user_id (FK → accounts_user)                              │
│ • duty_type (green_field, break, etc.)                      │
│ • assigned_date                                             │
│ • due_date                                                  │
│ • status (pending, completed, overdue)                      │
│ • notes                                                     │
│ • created_at, updated_at                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Communications                             │
├─────────────────────────────────────────────────────────────┤
│ announcements_announcement                                  │
│ • id (PK)                                                   │
│ • title                                                     |
│ • content                                                   │
│ • author_id (FK → accounts_user)                            │
│ • target_role_id (FK → accounts_role) [nullable]            │
│ • is_published                                              │
│ • published_date                                            │
│ • created_at, updated_at                                    │
│                                                             │
│ meetings_meeting                                            │
│ • id (PK)                                                   │
│ • title                                                     │
│ • date_time                                                 │
│ • location                                                  │
│ • description                                               │
│ • organizer_id (FK → accounts_user)                         │
│ • created_at, updated_at                                    │
│                                                             │
│ notifications_notification                                  │
│ • id (PK)                                                   │
│ • recipient_id (FK → accounts_user)                         │
│ • subject                                                   │
│ • message                                                   │
│ • email_sent                                                │
│ • sent_at                                                   │
│ • created_at                                                │
└─────────────────────────────────────────────────────────────┘
```

---

## API Reference

Post your username and password to the login endpoint to receive JWT tokens:

```http
POST /api/accounts/login/
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password"
}

Response: {
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Include the access token in the Authorization header for subsequent requests:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

The public API returns data without authentication required:

```http
GET /api/clubs/                    # List all active clubs
GET /api/clubs/?status=active      # Filter clubs by status
GET /api/clubs/?search=photography # Search clubs by name
GET /api/clubs/?page=2             # Fetch page 2 of results
GET /api/clubs/5/                  # Retrieve single club details
```

Protected endpoints require valid JWT authentication:

```http
GET /api/accounts/me/              # Current user's profile
GET /api/duty-roster/              # User's assigned duties
GET /api/announcements/            # All announcements visible to user
GET /api/announcements/3/          # Single announcement details
POST /api/clubs/                   # Create club (requires admin role)
PUT /api/clubs/5/                  # Update club (requires admin role)
DELETE /api/clubs/5/               # Delete club (requires admin role)
GET /api/meetings/                 # List scheduled meetings
POST /api/meetings/                # Create new meeting (requires permission)
GET /api/competitions/             # List competitions
POST /api/competitions/            # Create competition (requires permission)
```

---

## Deployment Architecture

The production environment uses Nginx as a reverse proxy receiving all incoming HTTP and HTTPS requests. Nginx terminates SSL connections, serves static files directly, and forwards API requests to multiple Gunicorn worker processes running the Django application.

Behind Gunicorn, the application connects to PostgreSQL for data persistence, Redis for caching and message brokering, Celery worker processes for background job execution, and external email services (such as SendGrid) for transactional emails.

```
┌──────────────────────────────────────────────────────────────┐
│                     Reverse Proxy (Nginx)                    │
│                   • HTTPS/SSL Termination                    │
│                   • Static File Serving                      │
│                   • Load Balancing                           │
└────────┬─────────────────────────────────────────────────────┘
         │
┌────────▼──────────────────────────────────────────────────────┐
│              Application Layer (Gunicorn)                     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  Django Application (Multiple Workers)                 │   │
│  │  • Process 1  • Process 2  • Process 3  • Process N    │   │
│  └────────────────────────────────────────────────────────┘   │
└────────┬──────────────────────────────────────────────────────┘
         │
    ┌────┴────┬─────────────────┬──────────────────┐
    │         │                 │                  │
┌───▼───┐  ┌──▼────────┐  ┌─────▼──────┐  ┌──────▼─────┐
│ PgSQL │  │   Redis   │  │ Email SMTP │  │   Celery   │
│       │  │ (Cache)   │  │  (Sendgrid)│  │  (Workers) │
└───────┘  └───────────┘  └────────────┘  └────────────┘
```

Before deploying to production, verify the following items:

- Configure Nginx reverse proxy with SSL certificates
- Set up Gunicorn with adequate worker processes (typically 2-4 per CPU core)
- Configure PostgreSQL with automated daily backups
- Set up Redis cluster for caching and message brokering
- Configure email service provider credentials (SendGrid, AWS SES, etc.)
- Enable HTTPS/TLS with valid SSL certificates
- Set up application monitoring and error logging
- Configure CI/CD pipeline for automated deployments
- Set up automated backup jobs with off-site storage
- Configure firewall rules to restrict access to necessary ports only

---

## Maintenance Procedures

Daily maintenance tasks verify that all services remain operational and responsive.

```bash
# Check Django logs for errors
tail -f /var/log/student-council/django.log

# Inspect active Celery tasks
celery -A student_council inspect active

# Count current database connections
psql -c "SELECT count(*) FROM pg_stat_activity;"

# Verify all services are running
systemctl status gunicorn
systemctl status celery-worker
systemctl status celery-beat
systemctl status redis-server
systemctl status postgresql
```

Watch for ERROR and WARNING entries in the logs that indicate problems with the application, database, or services.

Weekly maintenance includes database optimization and backup verification.

Run these commands weekly:

```bash
# Analyze and optimize database tables
vacuumdb -U postgres student_council_db

# Check table sizes to identify growth
psql -U postgres student_council_db -c "
  SELECT schemaname, tablename, 
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) 
  FROM pg_tables 
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Create compressed database backup
pg_dump -U postgres student_council_db | gzip > /backups/db_$(date +%Y%m%d).sql.gz

# Search logs for errors and warnings
grep ERROR /var/log/student-council/*.log
grep WARNING /var/log/student-council/*.log
```

Monthly maintenance includes data cleanup and security updates.

Monthly tasks:

```bash
# Remove notifications older than 6 months
python manage.py shell << EOF
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification

old_date = timezone.now() - timedelta(days=180)
Notification.objects.filter(created_at__lt=old_date).delete()
EOF

# Update Python packages to latest versions
pip install --upgrade -r requirements.txt

# Scan for security vulnerabilities in dependencies
pip-audit

# Update system packages
apt update && apt upgrade -y

# Analyze slow queries to identify performance issues
psql -c "SELECT query, calls, mean_time FROM pg_stat_statements 
         ORDER BY mean_time DESC LIMIT 10;"

# Review index usage to find unused or missing indexes
psql -c "SELECT schemaname, tablename, indexname 
         FROM pg_indexes 
         WHERE schemaname NOT IN ('pg_catalog', 'information_schema');"
```

---

## Monitoring & Logging

The application writes logs to `/var/log/student-council/django.log` with a rotating file handler that creates a new file when the current log reaches 10MB. The system keeps 10 rotated backup log files before deleting the oldest one.

Log messages include a level that indicates severity: DEBUG contains development information, INFO contains general operational messages, WARNING indicates potential problems that don't prevent the system from running, ERROR indicates failures that may impact functionality, and CRITICAL indicates system failures that require immediate attention.

Configure logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/student-council/django.log',
            'maxBytes': 1024*1024*10,  # 10MB
            'backupCount': 10,
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

Monitor these key metrics for system health:

| Metric | Target | Alert If Exceeded |
|--------|--------|-----------------|
| CPU Usage | Below 70% | 85% |
| Memory Usage | Below 80% | 90% |
| Disk Usage | Below 80% | 90% |
| Database Connections | Below 80 | 100 |
| Response Time | Below 200ms | 500ms |
| Error Rate | Below 1% | 5% |
| Celery Queue Length | Below 100 | 500 |

When any metric exceeds the alert threshold, investigate immediately. Start with the logs to understand what changed. For database issues, check connection counts and running queries. For memory issues, identify the largest processes and consider restarting them. For response time issues, run EXPLAIN ANALYZE on slow queries to find missing indexes.

---

## Backup & Recovery

The production environment backs up the database and uploaded media files daily. These backups are compressed and uploaded to cloud storage for off-site redundancy.

Automated daily backup script:

```bash
# Backup database
pg_dump -U postgres student_council_db | gzip > /backups/daily/db_$(date +%Y%m%d).sql.gz

# Backup uploaded media
tar -czf /backups/daily/media_$(date +%Y%m%d).tar.gz /path/to/media/

# Upload to cloud storage
aws s3 cp /backups/daily/db_*.sql.gz s3://backup-bucket/daily/
aws s3 cp /backups/daily/media_*.tar.gz s3://backup-bucket/daily/
```

If the database becomes corrupted or data is accidentally deleted, restore from a backup following these steps:

1. Stop the application to prevent new writes
2. Restore the database from the backup file
3. Run any pending migrations
4. Restart the application

Restore database commands:

```bash
# 1. Stop application
systemctl stop gunicorn celery-worker

# 2. Restore from backup (replace date with desired backup)
psql -U postgres student_council_db < /backups/db_20260326.sql

# 3. Run migrations if needed
python manage.py migrate

# 4. Restart application
systemctl start gunicorn celery-worker
```

The system maintains backup redundancy with the following recovery objectives:

- Recovery Time Objective (RTO): 30 minutes — Time to restore and bring system back online
- Recovery Point Objective (RPO): 24 hours — Maximum data loss is one day of changes

Daily backups retain a 30-day history. Weekly backups retain a 3-month history. Monthly backups are archived indefinitely.

---

## Troubleshooting Guide

If the application cannot connect to the database, PostgreSQL may not be running or the connection string may be incorrect.

Check PostgreSQL status:

```bash
systemctl status postgresql
```

If PostgreSQL is not running, start it:

```bash
systemctl start postgresql
```

Verify the service is listening on port 5432:

```bash
netstat -tlnp | grep 5432
```

Check the PostgreSQL error logs:

```bash
journalctl -u postgresql -n 20
```

When Celery background tasks do not process, Redis may be down or the Celery worker may have crashed.

Inspect active Celery tasks:

```bash
celery -A student_council inspect active
```

Test the Redis connection:

```bash
redis-cli ping
```

The response should be PONG. If Redis is not responding, restart it:

```bash
systemctl restart redis-server
```

Restart the Celery worker:

```bash
systemctl restart celery-worker
```

Watch out — if you see stuck tasks that will not process, clear them with:

```bash
celery -A student_council purge
```

When the server consumes excessive memory, identify which processes are using the most:

```bash
free -h
ps aux --sort=-%mem | head -10
```

If Gunicorn or Celery are consuming most of the memory, restart them:

```bash
systemctl restart gunicorn
systemctl restart celery-worker
```

Monitor memory usage after restart to see if it remains high or returns to normal.

When API responses are slow, database queries may be inefficient or missing indexes. Enable query logging to see which queries execute:

```bash
python manage.py shell
from django.db import connection
# Make request
print(connection.queries)
```

Check for indexes on frequently queried columns:

```bash
psql -c "SELECT * FROM pg_stat_user_indexes ORDER BY idx_scan ASC;"
```

Run EXPLAIN ANALYZE on slow queries to find bottlenecks:

```bash
psql -c "EXPLAIN ANALYZE SELECT * FROM clubs_club WHERE status='active';"
```

If a query has a high execution cost, add indexes on the filtered or joined columns.

---

## Version Control & Deployment

Follow this Git workflow for feature development:

```bash
# 1. Create feature branch
git checkout -b feature/new-feature

# 2. Make changes to code
# ... edit files ...

# 3. Stage and commit changes
git add .
git commit -m "Add new feature"

# 4. Push to repository
git push origin feature/new-feature

# 5. Create pull request on GitHub for code review
# ... wait for approval ...

# 6. Merge approved changes to main branch
git checkout main
git merge feature/new-feature
git push origin main
```

Deploying to production requires these steps:

```bash
# 1. Pull latest code from main branch
git pull origin main

# 2. Update Python package dependencies
pip install -r requirements.txt

# 3. Run database migrations
python manage.py migrate

# 4. Copy static files to serving directory
python manage.py collectstatic --noinput

# 5. Restart application services
systemctl restart gunicorn celery-worker

# 6. Verify deployment succeeded
curl http://localhost:8000/api/clubs/
```

After deployment, verify that the application responds correctly. Check the logs for any errors. Monitor resource usage for the first hour to ensure everything operates normally.

---

## Security Considerations

Store all secrets in environment variables and never commit `.env` files to the repository. Rotate secrets regularly and use dedicated secret management tools like HashiCorp Vault or AWS Secrets Manager in production.

Database connections must use strong passwords with at least 16 characters including uppercase, lowercase, numbers, and symbols. Enable SSL/TLS encryption for all database connections. Implement row-level security policies to restrict users from accessing data belonging to other organizations. Conduct regular security audits of database access patterns.

The API enforces HTTPS on all endpoints in production. Implement rate limiting on authentication endpoints to prevent brute force attacks. Validate all user inputs with Django serializers and form validation. Configure CORS to restrict which domains can access the API. Never trust user-supplied data.

Watch out — if you accept file uploads without validation, an attacker could upload malicious files. Always validate file types and sizes on the server side. Scan uploaded files with antivirus before storing them.

Keep all dependencies up to date. Run pip-audit monthly to find known vulnerabilities. Use SAST tools like Bandit and Pylint to identify code security issues. Implement code review for all pull requests. Run security tests as part of the CI/CD pipeline.

---

Documentation is located in `/path/to/docs/`. Report issues on GitHub. Contact hiba.malkan@gmail.com for questions or emergencies.

---

**Document Version:** 1.0  
**Last Updated:** March 26, 2026  
**Next Review:** June 26, 2026

---
