# Student Council Management System

![Python](https://img.shields.io/badge/python-3.13%2B-blue)
![Django](https://img.shields.io/badge/django-4.2-092e20)
![PostgreSQL](https://img.shields.io/badge/postgresql-12%2B-336791)
![License](https://img.shields.io/badge/license-source--available-lightgrey)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen)

A web application for managing student council operations, including clubs, competitions, meetings, duty rosters, announcements, discipline records, and gate pass requests. The system provides a role-based administrative dashboard for council members and a public-facing page listing active clubs, accessible without authentication.

## Overview

The application centralizes administrative workflows that were previously handled through disconnected tools. Council members manage duty rosters, announcements, competitions, meetings, and discipline records through a single dashboard. Students access a public club listing and submit signups without requiring an account. Role-based permissions determine what each user can view and modify, enforced independently on both the frontend and the backend API.

## Core Modules

**Clubs** — Public listing of active clubs with search and filtering. Administrators create, update, and manage club status.

**Duty Roster** — Monthly rotating duty assignments.

**Announcements** — Council-wide or role-targeted posts, with optional email notifications.

**Competitions** — Competition listings with participant signup tracking and deadline reminders.

**Meetings** — Scheduling, attendee management, and minutes of meeting storage, with automated reminder emails.

**Discipline** — Records of discipline violations with severity tracking and offense history.

**Gate Pass** — Student-submitted gate pass requests with an approval workflow and automated email notifications to students, parents, and class teachers.

**Notifications** — Scheduled (7:00 AM and 4:00 PM daily) and event-triggered email notifications, processed asynchronously via Celery.

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
