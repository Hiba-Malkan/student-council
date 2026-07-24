# Student Council Management System

![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![Django](https://img.shields.io/badge/django-4.2-092e20)
![PostgreSQL](https://img.shields.io/badge/postgresql-12%2B-336791)
![License](https://img.shields.io/badge/license-source--available-lightgrey)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)
![Tests](https://github.com/Hiba-Malkan/student-council/actions/workflows/tests.yml/badge.svg)
![Coverage](https://codecov.io/gh/Hiba-Malkan/student-council/branch/main/graph/badge.svg)

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#core-modules">Features</a> •
  <a href="#technology-stack">Tech Stack</a> •
  <a href="#documentation">Documentation</a> •
  <a href="#external-documentation">External Docs</a> •
  <a href="#license">License</a>
</p>

## Overview

This web application provides a single system of record for council administration. Duty assignments, meeting schedules and minutes, gate pass requests, announcements, and discipline records are stored and managed in one place, with automated email notifications replacing manual follow-up.

Permissions are defined as individual boolean fields on the Role model (`can_edit_duty_roster`, `can_schedule_meetings`, `can_manage_gatepass`, and so on) rather than hardcoded role names. Any role can be assigned any combination of permissions. Users without administrative permissions have read/signup-only access: viewing announcements, signing up for clubs and competitions, and submitting and tracking their own gate pass requests.

Permissions are enforced on both the frontend and the backend API independently. The frontend check controls what is rendered; the backend check controls what is executed.

## Quick Start

Requires Python 3.13+, Node.js 18+, PostgreSQL 12+, Redis, and Git.

```bash
git clone https://github.com/Hiba-Malkan/student-council.git
cd student-council/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Configure .env — see docs/LOCAL_DEVELOPMENT.md for variable reference

createdb student_council_db
python manage.py migrate
python manage.py createsuperuser

cd ../frontend
npm install
npx tailwindcss -i ./static/src/input.css -o ./static/dist/output.css
```

The application also requires a Celery worker, Celery Beat, and Redis running alongside the Django server. Full instructions, including role setup, are in the [Local Development Guide](./docs/LOCAL_DEVELOPMENT.md).

The app is served at `http://localhost:8000` once everything is running.

## Core Modules

**Duty Roster** — Users with the `can_edit_duty_roster` permission assign and manage duties for each council member from a central roster. Assignment and reminder emails are dispatched automatically ahead of each due date.

**Meetings** — Users with the `can_schedule_meetings` permission create meetings with an agenda attached. All council members are notified on creation, removing the need for manual outreach. Minutes of meeting, including action items and attendance, are recorded and stored per meeting after it concludes.

**Gate Pass** — Students submit gate pass requests through a single form. Requests route immediately to users with the `can_manage_gatepass` permission for approval or denial, with parents notified automatically once a decision is made. Daily and monthly activity summaries are generated automatically for administrative reference.

**Announcements** — Users with the `can_create_announcements` or `can_edit_announcements` permission publish announcements under defined categories, such as internal house, cultural, or urgent. Categorization keeps council-wide communication organized and searchable.

**Discipline Management** — Users with the `can_record_discipline` permission log violations against a student's existing history or create a new record for a first offense. A student's fourth recorded violation triggers an automatic notification to school leadership and discipline staff, removing the need for manual review of past records to catch repeat offenders. Viewing records requires the separate `can_view_discipline` permission.

**Clubs** — Users with the `can_add_clubs` permission create and maintain club listings, including required details for each. Centralized management supports club visibility and participation across the school.

**Competitions** — Users with the `can_manage_competitions` permission list competitions the school is entering, giving students visibility into what's available and when. Students register directly through the site, submitting their details and, where applicable, a team name. Registrations are visible to staff in real time, so participation can be tracked and support coordinated without a separate manual sign-up process.

**Students** — Users without an administrative role can view announcements, register for clubs and competitions, and submit and track gate pass requests, with no elevated permissions required.

## Technology Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2, Django REST Framework |
| Database | PostgreSQL 12+ |
| Task Queue | Celery with Celery Beat |
| Message Broker | Redis |
| Authentication | JWT (djangorestframework-simplejwt) |
| Frontend | HTML5, Tailwind CSS, vanilla JavaScript (ES6+) |
| Production Server | Gunicorn behind Nginx |

## Documentation

| Document | Description |
|---|---|
| [Local Development Guide](./docs/LOCAL_DEVELOPMENT.md) | Environment setup, running services, development workflow, API testing, troubleshooting |
| [System Documentation](./docs/SYSTEM_DOCUMENTATION.md) | Architecture, codebase structure, data model, full API reference |
| [Production Documentation](./docs/PRODUCTION_DOCUMENTATION.md) | Server setup, deployment, security hardening, backups, scaling |
| [Styling Guide](./docs/STYLING_GUIDE.md) | Tailwind CSS conventions, dark mode, modal and component patterns |

Start with the Local Development Guide to get a working environment. Refer to System Documentation for architecture and API details, and Production Documentation before deploying.

## Project Structure

```
student-council/
├── backend/                    Django application
│   ├── accounts/                User authentication and role management
│   ├── clubs/                   Club listings and signups
│   ├── duty_roster/              Duty assignments
│   ├── announcements/            Announcements
│   ├── competitions/              Competition management
│   ├── meetings/                  Meeting scheduling and minutes
│   ├── discipline/                Discipline records
│   ├── gatepass/                  Gate pass requests
│   ├── notifications/             Email notifications and Celery tasks
│   └── student_council/           Project settings, URLs, Celery config
│
├── frontend/                   Templates and static assets
│   ├── templates/
│   └── static/
│
└── docs/                       Documentation (see table above)
```

## External Documentation

| Technology | Documentation |
|---|---|
| Django | [docs.djangoproject.com](https://docs.djangoproject.com/) |
| Django REST Framework | [django-rest-framework.org](https://www.django-rest-framework.org/) |
| PostgreSQL | [postgresql.org/docs](https://www.postgresql.org/docs/) |
| Celery | [docs.celeryq.dev](https://docs.celeryq.dev/) |
| Redis | [redis.io/docs](https://redis.io/docs/latest/) |
| Tailwind CSS | [tailwindcss.com/docs](https://tailwindcss.com/docs) |
| djangorestframework-simplejwt | [django-rest-framework-simplejwt.readthedocs.io](https://django-rest-framework-simplejwt.readthedocs.io/) |
| Gunicorn | [docs.gunicorn.org](https://docs.gunicorn.org/) |
| Nginx | [nginx.org/en/docs](https://nginx.org/en/docs/) |

## License

See [docs/LICENSE.md](./docs/LICENSE.md) for full license terms. For permission requests, contact hiba.malkan@gmail.com.

## Support

Consult the relevant document in `docs/` before submitting a support request, as most setup and troubleshooting issues are addressed there. Bug reports should be filed as GitHub issues. For other inquiries, contact hiba.malkan@gmail.com.

---

**Maintained by:** Hiba
**Last Updated:** July 2026