# 🎓 STUDENT MODE - How It Works

## Overview

A **Student** is a user with login credentials who can view content but has **NO admin permissions**.

---

## Student Mode Features

### ✅ Students CAN:
- Login with username/password
- View announcements
- View all clubs
- View all competitions
- **Sign up for clubs** (without any special permission)
- **Sign up for competitions** (without any special permission)
- View meetings
- View their own profile
- View notifications

### ❌ Students CANNOT:
- Access Dashboard (`/dashboard/`) - **Hidden from sidebar**
- View Duty Roster (`/duty-roster/`) - **Hidden from sidebar**
- View Discipline Records - **Hidden from sidebar**
- Create announcements
- Create clubs
- Edit any content
- Delete any content
- Create competitions
- Manage any system features
- Access Admin Panel (`/admin/`)

---

## Navigation for Students vs Admins

### **Student Navigation (Normal Student)**
```
📌 Announcements
🏫 Clubs
🏆 Competitions
📅 Meetings
ℹ️  About
👤 Profile
```

### **Admin Navigation (C-Suite/Manager)**
```
📊 Dashboard              ← Hidden for students
📌 Announcements
🏫 Clubs
🏆 Competitions
📅 Meetings
⚠️  Discipline            ← Hidden for students
📋 Duty Roster            ← Hidden for students
ℹ️  About
👤 Profile
⚙️  Admin Panel           ← Hidden for students
```

---

## User Interface Behavior

### Clubs Page

**For Students:**
```
[Search clubs...] [Filter by status]

📱 Club Name
   Description of the club...
   Founders: ...
   Tutors: ...
   Members: 50
   
   [Join Club] ← Button visible, can click to sign up
```

**For Club Managers:**
```
[Search clubs...] [Filter by status] [✚ Create New Club] ← Visible

📱 Club Name
   Description of the club...
   Founders: ...
   Tutors: ...
   Members: 50
   
   [✎ Edit] [🗑 Delete] [Join Club] ← All buttons visible
```

### Announcements Page

**For Students:**
```
[Search announcements...] [Filter by type]

📌 Announcement Title
   This is the announcement content...
   Published: 2026-03-26
   Type: Event
```

**For Announcement Admins:**
```
[Search announcements...] [Filter by type] [✚ New Announcement]

📌 Announcement Title
   This is the announcement content...
   Published: 2026-03-26
   Type: Event
   
   [✎ Edit] [🗑 Delete]
```

---

## How to Test Student Mode

### 1. Login as Student
```
Username: teststudent
Password: student123
```

### 2. Observe Student Experience
- ✅ Can see `/clubs/` page
- ✅ Can see `/announcements/` page
- ✅ Can see `/competitions/` page
- ❌ Dashboard link is GONE from sidebar
- ❌ Duty Roster link is GONE from sidebar
- ❌ Discipline link is GONE from sidebar
- ❌ No "Create New Club" button visible
- ❌ No Edit/Delete buttons on clubs
- ✅ "Join Club" button IS visible and clickable

### 3. Try to Access Restricted Pages
```
Try to visit: http://localhost:8000/dashboard/
Result: Page may load but shows error or empty (backend will reject it)

Try to visit: http://localhost:8000/duty-roster/
Result: Error: IsAuthenticated permission denied
```

### 4. Try to Sign Up for Club
```
1. Click "Join Club" button on a club card
2. Modal appears with form
3. Fill in: Name, Email, (Phone optional, Message optional)
4. Click "Send Join Request"
5. ✅ Success! "Thank you, you'll be contacted soon"
```

---

## Technical Implementation

### 1. Role Model
```python
class Role(models.Model):
    name = "Student"
    is_normal_student = True  # Key field!
    
    # All permissions are False:
    can_add_clubs = False
    can_create_announcements = False
    can_edit_announcements = False
    can_edit_duty_roster = False
    can_schedule_meetings = False
    can_record_discipline = False
    can_view_discipline = False
    can_manage_competitions = False
```

### 2. Frontend Navigation Control (base.html)
```javascript
// Hide dashboard and duty roster for normal students
if (userData.role_detail?.is_normal_student) {
    document.getElementById('dashButton').style.display = 'none';
    document.getElementById('dutyButton').style.display = 'none';
    document.getElementById('disciplineButton').style.display = 'none';
}
```

### 3. Template Permission Checks (clubs.html)
```javascript
// Only show Create Club button if user has permission
if (userData.is_superuser || userData.role_detail?.can_add_clubs) {
    document.getElementById('createClubSection').style.display = 'block';
}
```

### 4. API Endpoint Protection
```python
# Clubs API - view is open to authenticated users
GET /api/clubs/ → IsAuthenticated (students can view)

# But create/edit/delete requires permission
POST /api/clubs/ → IsAuthenticated + CanManageClubs
PUT /api/clubs/{id}/ → IsAuthenticated + CanManageClubs
DELETE /api/clubs/{id}/ → IsAuthenticated + CanManageClubs

# Public signup endpoints (no permission needed)
POST /api/clubs/{id}/join/ → AllowAny (anyone can signup)
POST /api/competitions/{id}/signup/ → AllowAny (anyone can signup)
```

---

## Security Model

### ✅ What Makes Students Secure

1. **Frontend + Backend validation**
   - Buttons hidden in UI (frontend)
   - API checks permissions (backend - important!)
   - Can't edit HTML to fake permissions

2. **Role-Based Access Control (RBAC)**
   - Student role has NO admin permissions
   - Can't grant yourself permissions
   - Only superuser/staff can change roles

3. **Authentication Required**
   - Students must login (unlike public visitors)
   - JWT token expires
   - API validates token on each request

4. **No Direct Database Access**
   - Students use REST API only
   - API has permission checks
   - Database constraints enforced

---

## Permission Hierarchy

```
Public (no login)
↓
Student (login, is_normal_student=True, no permissions)
↓
Manager (login, specific admin permissions like can_add_clubs)
↓
C-Suite / Admin (login, is_staff=True or is_superuser=True, all permissions)
```

---

## Test Scenarios

### Scenario 1: Student tries to view clubs
```
1. Login as teststudent
2. Click "Clubs" in navigation
3. Page loads with club list
4. Can search and filter clubs
5. Click "Join Club" → Modal opens
6. ✅ SUCCESS: Can sign up
```

### Scenario 2: Student tries to edit a club
```
1. Login as teststudent
2. Go to clubs page
3. Look for Edit button on club card
4. ❌ No Edit button visible
5. Even if they try to manually navigate to /clubs/edit/1/
   → Page loads but empty or error (backend rejects without permission)
```

### Scenario 3: Student tries to access dashboard
```
1. Login as teststudent
2. Look at sidebar navigation
3. ❌ Dashboard link is completely hidden
4. If they try to manually navigate to /dashboard/
   → Page may load but will be empty/error or show restricted message
```

### Scenario 4: Manager tries to create club
```
1. Login as club_manager (has can_add_clubs permission)
2. Go to clubs page
3. ✅ "Create New Club" button IS visible
4. Click it → Form opens
5. Can create new club
```

---

## Summary

**Student Mode = Authenticated View-Only User**

| Feature | Public Visitor | Student | Manager | Admin |
|---------|---|---|---|---|
| Login Required | ❌ | ✅ | ✅ | ✅ |
| View Clubs | ❌ | ✅ | ✅ | ✅ |
| Join Club | ❌ | ✅ | ✅ | ✅ |
| Create Club | ❌ | ❌ | ✅ | ✅ |
| Dashboard | ❌ | ❌ | ✅ | ✅ |
| Duty Roster | ❌ | ❌ | ✅ | ✅ |
| Admin Panel | ❌ | ❌ | ❌ | ✅ |

---

## Files Modified

- `frontend/templates/base.html` - Added logic to hide sidebar items for students
- `backend/accounts/models.py` - Uses existing Role model with is_normal_student field
- `backend/clubs/views.py` - Already checks can_add_clubs permission
- `backend/announcements/views.py` - Already checks can_create_announcements permission

**No public pages!** Everything requires login now. Students just have limited permissions.
