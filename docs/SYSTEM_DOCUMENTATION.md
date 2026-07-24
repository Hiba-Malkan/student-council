# System Documentation

**Version:** 1.1
**Last Updated:** July 2026
**Status:** Production Ready

This document describes the architecture, codebase structure, data model, and API surface of the Student Council Management System.

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Authentication and Authorization](#authentication-and-authorization)
3. [Codebase Structure](#codebase-structure)
4. [Module Documentation](#module-documentation)
5. [Data Model](#data-model)
6. [API Reference](#api-reference)

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  Web Browser (HTML, CSS, JavaScript, Tailwind CSS)               │
│  Dashboard · Admin Panel · Public Pages                          │
└─────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/HTTPS
┌─────────────────────▼──────────────────────────────────────────┐
│                    API Layer                                     │
│  Django REST Framework                                           │
│  REST Endpoints (/api/*) · JWT Authentication ·                  │
│  Serializers & Validation · Permission Classes                   │
└─────────┬──────────────────────────────────────┬────────────────┘
          │ SQL                                  │ Tasks
┌─────────▼──────────────────┐  ┌────────────────▼──────────────┐
│   PostgreSQL Database       │  │  Message Queue System          │
│  Users & Roles · Clubs      │  │  Redis (Message Broker)        │
│  Duties · Announcements     │  │  Celery (Task Queue)           │
│  Competitions · Meetings    │  │  Celery Beat (Scheduler)       │
│  Discipline · Notifications │  │                                 │
│                              │  │  Background Jobs:              │
│                              │  │  Email Notifications           │
│                              │  │  Duty Cycling                  │
│                              │  │  Scheduled Tasks               │
└──────────────────────────────┘  └─────────────────────────────┘
```

The frontend is server-rendered HTML with Tailwind CSS for styling and vanilla JavaScript (ES6+) for interactivity — there is no frontend framework. The backend runs Django 4.2 with Django REST Framework delivering the API. PostgreSQL 12+ is the primary data store. Redis handles message brokering for Celery, which processes background tasks and, via Celery Beat, scheduled tasks. Authentication uses JWT via djangorestframework-simplejwt for stateless request validation. In production, Gunicorn serves the Django application behind Nginx, which terminates SSL and serves static files directly.

## Authentication and Authorization

### JWT Authentication Flow

1. The user submits credentials to `/api/accounts/login/`.
2. The backend validates credentials and returns an access token and a refresh token.
3. The frontend stores both tokens in `localStorage`.
4. Subsequent API requests include the access token in the `Authorization` header as `Bearer {access_token}`.
5. The backend validates the JWT signature and expiration on every request.
6. Expired access tokens are refreshed using the refresh token.
7. On logout, the frontend clears `localStorage`; the tokens themselves are not revoked server-side.

### Role-Based Permissions

The `accounts_role` model uses boolean permission fields rather than hardcoded role names, which keeps access control flexible without requiring code changes when new roles are introduced.

| Field | Grants |
|---|---|
| `is_normal_student` | Identifies regular students; blocks access to restricted features |
| `can_edit_duty_roster` | Create and edit duty assignments |
| `can_schedule_meetings` | Schedule meetings |
| `can_create_announcements` | Create announcements |
| `can_edit_announcements` | Edit existing announcements |
| `can_record_discipline` | Add and edit discipline records |
| `can_view_discipline` | View discipline records |
| `can_add_clubs` | Create clubs |
| `can_manage_competitions` | Create and edit competitions |
| `can_manage_gatepass` | View, approve, and deny gate pass requests |
| `show_in_duty_roster` | Eligible to appear in duty roster rotation |

### Frontend Authorization Pattern

Protected pages check role permissions on load before rendering restricted content:

```javascript
await loadUserProfile();
const isNormalStudent = userData?.role?.is_normal_student;

if (isNormalStudent) {
    showError('You do not have permission to access this page');
    setTimeout(() => window.location.href = '/announcements/', 1500);
    return;
}

if (userData.role?.can_schedule_meetings || userData.is_staff) {
    // Render meeting scheduling controls
}
```

### Protected Pages

| Page | Restriction | Requires |
|---|---|---|
| `/dashboard/` | Blocked for normal students | Non-student status |
| `/meetings/` | Blocked for normal students | `can_schedule_meetings` to create meetings |
| `/duty-roster/` | Blocked for normal students | `can_edit_duty_roster` to assign duties |
| `/discipline/`, `/discipline/detail/{id}/` | Blocked for normal students | `can_record_discipline` or staff status |
| `/clubs/signups/`, `/clubs/new/` | Signup view requires permission | `can_add_clubs` or club management permission |
| `/competitions/signups/`, `/competitions/new/`, `/competitions/edit/{id}/` | Signup view requires permission | `can_manage_competitions` or staff status |
| `/gatepass/` (admin section) | Admin panel hidden without permission | `can_manage_gatepass` |

### Backend Permission Classes

Every protected endpoint enforces permissions server-side via Django REST Framework permission classes, independent of frontend checks:

```python
class CanRecordDiscipline(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_staff or \
               request.user.role.can_record_discipline


class DisciplineViewSet(viewsets.ModelViewSet):
    permission_classes = [CanRecordDiscipline]
```

### Security Considerations

Frontend permission checks control what is rendered; backend permission classes control what is executed. A user cannot bypass restrictions by navigating directly to a protected URL, since the API independently validates every request. Staff and superuser accounts bypass role-based permission checks. Access tokens expire on a configurable interval (default 5 minutes) and must be refreshed. All production deployments must run over HTTPS. CORS is restricted to configured domains only.

### Authorization Flow

```
User Login
    │
    ▼
Backend validates credentials
    │
    ▼
Returns JWT tokens + user data with role
    │
    ▼
Frontend stores tokens in localStorage
    │
    ▼
User accesses a protected page
    │
    ├── userData.role.is_normal_student = true
    │       → Show error, redirect to /announcements/
    │
    └── userData.role.is_normal_student = false
            → Load page content
            → Check feature-specific permissions
            → Show or hide individual features accordingly
    │
    ▼
API requests include Authorization header with JWT
    │
    ▼
Backend validates token signature and expiration
    │
    ├── Invalid or expired → 401 Unauthorized
    │
    └── Valid → Check endpoint permission class
            ├── Authorized → Execute request
            └── Denied → 403 Forbidden
```

## Codebase Structure

```
student-council/
│
├── backend/
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env
│   │
│   ├── student_council/              Project package
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   ├── celery.py
│   │   └── asgi.py
│   │
│   ├── accounts/                     Authentication and users
│   │   ├── models.py                  User, Role
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── clubs/                        Club management
│   │   ├── models.py                  Club, ClubSignup
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── admin.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── duty_roster/                  Duty management
│   │   ├── models.py                  Duty, DutyType
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── permissions.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── announcements/                Announcements
│   │   ├── models.py                  Announcement
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── competitions/                 Competitions
│   │   ├── models.py                  Competition, CompetitionSignup
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── migrations/
│   │
│   ├── meetings/                     Meetings
│   │   ├── models.py                  Meeting, MeetingAttendance, MinutesOfMeeting
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── migrations/
│   │
│   ├── discipline/                   Discipline records
│   │   ├── models.py                  DisciplineRecord, OffenseLog
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── migrations/
│   │
│   ├── gatepass/                     Gate pass requests
│   │   ├── models.py                  GatePass
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── migrations/
│   │
│   ├── notifications/                Email notifications
│   │   ├── models.py                  Notification, NotificationBatch, EmailTemplate
│   │   ├── tasks.py                   Celery tasks
│   │   ├── signals.py                 Django signals
│   │   ├── utils.py                   Email utilities
│   │   ├── views.py
│   │   └── migrations/
│   │
│   └── media/                        Uploaded files
│       ├── announcements/
│       ├── club_logos/
│       ├── competitions/
│       └── meetings/
│
├── frontend/
│   ├── templates/
│   │   ├── base.html                  Main template with navigation
│   │   ├── public_base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── forgot_password.html
│   │   ├── clubs/
│   │   ├── announcements/
│   │   ├── duty-roster/
│   │   ├── competitions/
│   │   ├── meetings/
│   │   └── discipline/
│   │
│   ├── static/
│   │   ├── dist/output.css            Compiled Tailwind
│   │   ├── src/input.css              Tailwind source
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   │
│   ├── package.json
│   └── tailwind.config.js
│
└── docs/
```

## Module Documentation

### Accounts

Handles authentication and role management. Implements JWT-based auth with role-based access control; users log in with credentials and receive access and refresh tokens for subsequent requests.

Role types:

**Student** — Default role for all registered users. View clubs, browse announcements, sign up for competitions and clubs. No create or edit access.

**Captain** — Assigned to team captains or event leaders. All Student permissions plus competition management and signup visibility.

**Class Representative** — Assigned to class representatives. All Student permissions plus extended organizational capabilities, depending on assigned permissions.

**C-Suite** (President, Vice President, Secretary, Treasurer) — Edit the duty roster, schedule meetings, create and edit announcements, view discipline records, manage competitions and signups, and assign roles to other users. Role assignment is restricted to C-Suite members.

Database tables: `accounts_user`, `accounts_role`.

### Clubs

Manages student organizations. Administrators with the appropriate permission create, edit, and delete clubs. Club status is one of active, under review, or inactive.

Each club stores a name, description, logo, founding year, and member count. The public API endpoint returns active clubs without authentication, powering the public clubs page. Admin endpoints require authentication and the relevant permission.

Database tables: `clubs_club`, `clubs_clubsignup`.

### Duty Roster

Assigns rotating maintenance duties to students. Each duty has a type, a date, a location, and a completion status. Duties cycle at the start of each month; overdue duties are flagged for administrator visibility.

Database tables: `duty_roster_duty`, `duty_roster_dutytype`.

### Announcements

Allows administrators to post news to the council or to specific roles. Each announcement has a title, content, publication status, and optional event details (date, time, location, registration deadline). Announcements can trigger an email send and support attachments.

Database tables: `announcements_announcement`, `announcements_announcement_target_roles`, `announcements_announcement_target_users`.

### Notifications

Sends email notifications on a schedule and in response to events. Celery tasks in `tasks.py` handle delivery asynchronously so HTTP requests are not blocked on email sending. Django signals trigger notifications automatically when announcements are published, duties are assigned, or meetings are scheduled. Scheduled tasks run twice daily, at 7:00 AM and 4:00 PM, to process pending notifications.

Key background tasks: sending announcement emails to targeted roles, sending daily duty reminders for overdue tasks, and sending event notifications for upcoming meetings and competitions.

Database tables: `notifications_notification`, `notifications_notificationbatch`, `notifications_emailtemplate`.

### Competitions

Lets administrators create and manage competitions, each with a title, description, dates, and participation requirements. Students sign up with a name, email, phone number, and optional team name or message. Administrators manage signups through `/competitions/signups/`, including removal via a confirmation modal — see the Signup Management section below and `STYLING_GUIDE.md` for the modal pattern.

Database tables: `competitions_competition`, `competitions_competitionsignup`.

### Signup Management

Handles registrations for both competitions and clubs. Students enter through a form requiring name, email, phone number, and an optional team name (competitions only) or message.

Administrators view signups at `/competitions/signups/` and `/clubs/signups/`, paginated at 10 entries per page. Each row shows name, email, phone, team name (competitions), a message button, signup date, and a delete action.

Deleting a signup opens a confirmation modal displaying the student's name in red text, with Cancel and Delete actions centered in the footer. The modal follows the light/dark styling pattern documented in `STYLING_GUIDE.md`: white background with dark gray (`#111827`) text in light mode, `gray-900` background with white text in dark mode.

### Meetings

Schedules council meetings and tracks attendance. Each meeting has a date, time, location, and description, with optional reminder emails sent before the scheduled time. Minutes of meeting can be uploaded per meeting, along with present/absent attendee lists and action items.

Database tables: `meetings_meeting`, `meetings_meeting_attendees`, `meetings_meeting_attendee_roles`, `meetings_meetingattendance`, `meetings_minutesofmeeting`.

### Discipline

Records instances of policy violations. Each discipline record tracks a student, an offense count, and a linked offense log with category, reason, and date. The system maintains a running history per student for reference.

Database tables: `discipline_disciplinerecord`, `discipline_offenselog`.

### Gate Pass

Manages student gate pass requests and their approval workflow.

**Request submission** — Students submit a request with personal details (name, D.No, class, section), parent email, an optional class teacher email, requested date, and reason. Confirmation emails go to the student, parent, and class teacher on submission; gate pass managers are notified as well.

**Request management** — Administrators with `can_manage_gatepass` view a paginated, status-filtered list (pending, approved, denied) and approve or deny each request, optionally with a note.

**Approval workflow** — Approving or denying a request records the decision, timestamp, and approving administrator, then triggers decision emails to the student, parent, and class teacher.

**Access control** — `can_manage_gatepass` gates both request visibility (all requests vs. own requests only) and the approve/deny action, enforced on frontend and backend independently.

Database table: `gatepass_gatepass`.

```
gatepass_gatepass
• id (PK)
• student_id (FK → accounts_user)
• dno
• name
• student_class
• student_section
• parent_email
• ct_email (nullable)
• requested_date
• reason
• status                       pending | approved | denied
• approved_by_id (FK → accounts_user, nullable)
• approval_note (nullable)
• approval_timestamp (nullable)
• requested_at
• updated_at
```

**API endpoints**

```
GET /api/gatepass/
    Auth: required
    Admins (can_manage_gatepass) see all requests; students see only their own.
    Query params: ?status=pending|approved|denied
    Pagination: 5 per page

POST /api/gatepass/
    Auth: required
    Body: {
        "dno": "D10060",
        "name": "Alice Johnson",
        "student_class": "11",
        "student_section": "B",
        "parent_email": "alice.parent@email.com",
        "ct_email": "ct@school.com",
        "requested_date": "2026-08-25",
        "reason": "Medical appointment with specialist"
    }
    Returns: 201, created gate pass object. Triggers submission emails.

POST /api/gatepass/{id}/approve_or_deny/
    Auth: required, can_manage_gatepass
    Body: { "status": "approved" | "denied", "note": "Optional note" }
    Returns: 200, updated gate pass object. Triggers decision emails.
    Error: 403 if the user lacks can_manage_gatepass.

GET /api/gatepass/my_requests/
    Auth: required
    Returns: All requests submitted by the current user.

GET /api/gatepass/processed-requests/
    Auth: required, can_manage_gatepass
    Returns: Paginated approved/denied requests, ordered by approval timestamp.
    Pagination: 5 per page
    Error: 403 if the user lacks can_manage_gatepass.
```

**Example — submitting a request**

```
POST /api/gatepass/
Content-Type: application/json

{
    "dno": "D10060",
    "name": "Alice Johnson",
    "student_class": "11",
    "student_section": "B",
    "parent_email": "alice.parent@email.com",
    "ct_email": "ct@school.com",
    "requested_date": "2026-08-25",
    "reason": "Medical appointment with specialist"
}

Response (201 Created):
{
    "id": 42,
    "student": { "id": 15, "username": "alice123", "email": "alice@school.com", ... },
    "dno": "D10060",
    "name": "Alice Johnson",
    "student_class": "11",
    "student_section": "B",
    "parent_email": "alice.parent@email.com",
    "ct_email": "ct@school.com",
    "requested_date": "2026-08-25",
    "reason": "Medical appointment with specialist",
    "status": "pending",
    "status_display": "Pending",
    "approved_by": null,
    "approval_note": "",
    "approval_timestamp": null,
    "requested_at": "2026-07-18T10:30:00Z",
    "updated_at": "2026-07-18T10:30:00Z"
}
```

**Example — approving a request**

```
POST /api/gatepass/42/approve_or_deny/
Content-Type: application/json

{
    "status": "approved",
    "note": "Approved. Please collect gate pass from office."
}

Response (200 OK):
{
    "id": 42,
    "student": { ... },
    "status": "approved",
    "status_display": "Approved",
    "approved_by": { "id": 3, "username": "president", ... },
    "approval_note": "Approved. Please collect gate pass from office.",
    "approval_timestamp": "2026-07-18T11:15:00Z",
    "requested_at": "2026-07-18T10:30:00Z",
    "updated_at": "2026-07-18T11:15:00Z"
}
```

**Frontend and backend validation**

```javascript
// Frontend — hide admin controls if the permission is missing
if (!userData.role || !userData.role.can_manage_gatepass) {
    adminSection.style.display = 'none';
}
```

```python
# Backend — the authoritative check
def approve_or_deny(self, request, pk=None):
    if not self._can_manage_gatepass(request.user):
        return Response(
            {'error': 'You do not have permission...'},
            status=status.HTTP_403_FORBIDDEN
        )
```

The frontend check controls what is shown. The backend check is what actually prevents an unauthorized request from succeeding, regardless of what the frontend does or doesn't render.

## Data Model

### Users and Roles

```
accounts_user
• id (PK)
• username (unique)
• email (unique)
• password (hashed)
• first_name, last_name
• role_id (FK → accounts_role, nullable)
• phone, grade, section, house, is_phase_head
• avatar, bio
• is_active, is_staff, is_superuser
• date_joined, created_at, updated_at

accounts_role
• id (PK)
• name (unique)
• is_normal_student
• show_in_duty_roster
• can_edit_duty_roster
• can_schedule_meetings
• can_create_announcements
• can_edit_announcements
• can_record_discipline
• can_view_discipline
• can_add_clubs
• can_manage_competitions
• can_manage_gatepass
• created_at, updated_at
```

### Clubs

```
clubs_club
• id (PK)
• name
• description
• logo
• status                    active | under_review | inactive
• established_year, established_by, tutors
• member_count
• created_by_id (FK → accounts_user)
• created_at, updated_at

clubs_clubsignup
• id (PK)
• club_id (FK → clubs_club)
• student_name, email, phone, message
• created_at
```

### Duty Roster

```
duty_roster_duty
• id (PK)
• duty_type_id (FK → duty_roster_dutytype, nullable)
• assigned_to_id (FK → accounts_user)
• assigned_by_id (FK → accounts_user, nullable)
• date, location, subsidiary_area, instructions
• is_completed, completed_at, notes
• created_at, updated_at

duty_roster_dutytype
• id (PK)
• name (unique), description, location, color
• created_at, updated_at
```

### Communications

```
announcements_announcement
• id (PK)
• title, content, announcement_type
• target_houses, target_grades
• is_public, is_pinned
• event_date, event_time, event_location
• registration_required, registration_deadline
• attachments
• is_published, published_at
• send_email, email_sent, email_sent_at
• created_by_id (FK → accounts_user)
• created_at, updated_at

meetings_meeting
• id (PK)
• title, description, agenda
• date, location, meeting_link
• is_cancelled, cancellation_reason
• morning_reminder_sent
• organized_by_id (FK → accounts_user)
• created_at, updated_at

meetings_minutesofmeeting
• id (PK)
• meeting_id (FK → meetings_meeting, unique)
• content, action_items, document
• uploaded_by_id (FK → accounts_user)
• emailed_to_phase_heads, email_sent_at
• created_at, updated_at

notifications_notification
• id (PK)
• recipient_id (FK → accounts_user)
• notification_type, title, message, action_url
• is_read, read_at, is_snoozed, snoozed_until
• send_email, email_sent, email_sent_at
• created_at
```

## API Reference

### Authentication

```http
POST /api/accounts/login/
Content-Type: application/json

{
  "username": "president",
  "password": "password"
}

Response:
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

Include the access token on subsequent requests:

```http
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Public endpoints (no authentication)

```http
GET /api/clubs/
GET /api/clubs/?status=active
GET /api/clubs/?search=photography
GET /api/clubs/?page=2
GET /api/clubs/5/
GET /public/clubs/                                            Public clubs page (HTML, not API)
```

### Role management

```http
GET /api/roles/
    Auth: required
    Returns: List of available roles and their IDs, for use with assign_role.

POST /api/accounts/{user_id}/assign_role/
    Auth: required, C-Suite role only
    Body: { "role_id": 2 }
    Returns: Updated user object with the new role.
    Error: 403 if the requesting user is not C-Suite.
```

### Authenticated endpoints

```http
GET /api/accounts/me/
GET /api/duty-roster/
GET /api/announcements/
GET /api/announcements/3/

GET /api/competitions/
GET /api/competitions/5/signups/
POST /api/competitions/                                     Requires can_manage_competitions
DELETE /api/competitions/5/delete_signup/?signup_id=123      Requires C-Suite role

GET /api/clubs/
GET /api/clubs/8/signups/
POST /api/clubs/                                             Requires can_add_clubs
DELETE /api/clubs/8/delete_signup/?signup_id=456              Requires C-Suite role

PUT /api/clubs/5/                                             Requires C-Suite role
DELETE /api/clubs/5/                                          Requires C-Suite role
GET /api/meetings/
POST /api/meetings/                                           Requires can_schedule_meetings
```

Gate pass endpoints are documented in full under [Gate Pass](#gate-pass) above.

---

**Document Version:** 1.1
**Last Updated:** July 2026