# Quick Reference: CSS Classes Cheat Sheet

## 🎨 Badges

```html
<!-- Status Badges -->
<span class="badge badge-success">Completed</span>
<span class="badge badge-danger">Overdue</span>
<span class="badge badge-info">Today</span>
<span class="badge badge-warning">Pending</span>
<span class="badge badge-neutral">Upcoming</span>
<span class="badge badge-primary">Active</span>
```

**Use for:** Status indicators, labels, tags

---

## 🔘 Buttons

```html
<!-- Primary Action -->
<button class="btn btn-primary">Save</button>

<!-- Secondary Action -->
<button class="btn btn-secondary">Cancel</button>

<!-- Destructive Action -->
<button class="btn btn-danger">Delete</button>
```

**Use for:** Forms, actions, CTAs

---

## 📦 Cards

```html
<!-- Basic Card -->
<div class="card">
    <div class="card-header">
        <h2 class="card-title">Card Title</h2>
        <p class="card-subtitle">Optional subtitle</p>
    </div>
    <div>
        Card content goes here
    </div>
</div>
```

**Use for:** Content containers, sections

---

## 📝 Forms

```html
<!-- Form Group -->
<div class="form-group">
    <label class="form-label">Field Label</label>
    <input type="text" class="form-input" placeholder="Enter value">
</div>

<!-- Text Area -->
<div class="form-group">
    <label class="form-label">Description</label>
    <textarea class="form-input" rows="3"></textarea>
</div>

<!-- Select -->
<div class="form-group">
    <label class="form-label">Choose Option</label>
    <select class="form-input">
        <option>Option 1</option>
    </select>
</div>
```

**Use for:** All form elements

---

## 📊 Tables

```html
<!-- Table -->
<div class="table-container">
    <table class="table">
        <thead>
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
            </tr>
        </tbody>
    </table>
</div>
```

**Use for:** Data tables

---

## 👤 Avatars

```html
<!-- Small Avatar -->
<div class="avatar avatar-sm" style="background-color: #16a34a;">JD</div>

<!-- Medium Avatar -->
<div class="avatar avatar-md" style="background-color: #3b82f6;">AB</div>

<!-- Large Avatar -->
<div class="avatar avatar-lg" style="background-color: #ef4444;">CD</div>
```

**Use for:** User initials, profile pictures

---

## 📭 Empty States

```html
<div class="empty-state">
    <div class="empty-state-icon">
        <span class="material-icons-round">inbox</span>
    </div>
    <h3 class="empty-state-title">No Items Found</h3>
    <p class="empty-state-text">There are no items to display at this time.</p>
</div>
```

**Use for:** No data states

---

## 🎯 Duty Roster Specific

```html
<!-- Duty Card -->
<div class="card duty-card">
    <div class="duty-header">
        <h2 class="duty-greeting">Hello!</h2>
        <span class="badge badge-primary">Member</span>
    </div>
</div>

<!-- Duty Info Grid -->
<div class="duty-info-grid">
    <div class="duty-info-item">
        <span class="duty-info-label">Label</span>
        <span class="duty-info-value">Value</span>
    </div>
</div>

<!-- Duty Form -->
<form class="duty-form">
    <div class="duty-form-row">
        <!-- form fields -->
    </div>
</form>
```

---

## 📢 Announcements Specific

```html
<!-- Announcement Card -->
<div class="announcement-card">
    <div class="announcement-header">
        <h3 class="announcement-title">Title</h3>
    </div>
    <div class="announcement-content">
        Content here
    </div>
    <div class="announcement-footer">
        Footer info
    </div>
</div>

<!-- Filters -->
<div class="announcement-filters">
    <button class="announcement-filter-btn active">All</button>
    <button class="announcement-filter-btn">Important</button>
</div>
```

---

## 🤝 Meetings Specific

```html
<!-- Meeting Card -->
<div class="meeting-card">
    <div class="meeting-header">
        <h3 class="meeting-title">Meeting Title</h3>
        <span class="meeting-status upcoming">Upcoming</span>
    </div>
    <div class="meeting-info">
        <div class="meeting-info-row">
            <span class="material-icons-round meeting-info-icon">event</span>
            <span>Date & Time</span>
        </div>
    </div>
</div>

<!-- Attendees -->
<div class="meeting-attendees-list">
    <div class="meeting-attendee">John Doe</div>
</div>
```

---

## 🏆 Clubs Specific

```html
<!-- Club Card -->
<div class="club-card">
    <div class="club-logo-container">
        <img src="logo.jpg" class="club-logo" alt="Logo">
    </div>
    <h3 class="club-name">Club Name</h3>
    <p class="club-category">Category</p>
    <p class="club-description">Description...</p>
    <div class="club-stats">
        <div class="club-stat">
            <div class="club-stat-value">50</div>
            <div class="club-stat-label">Members</div>
        </div>
    </div>
</div>

<!-- Grid -->
<div class="clubs-grid">
    <!-- club cards -->
</div>
```

---

## 🎖️ Competitions Specific

```html
<!-- Competition Card -->
<div class="competition-card">
    <div class="competition-image-container">
        <img src="img.jpg" class="competition-image">
        <span class="competition-status ongoing">Ongoing</span>
    </div>
    <h3 class="competition-title">Competition Name</h3>
    <div class="competition-stats">
        <div class="competition-stat">
            <div class="competition-stat-value">25</div>
            <div class="competition-stat-label">Participants</div>
        </div>
    </div>
</div>

<!-- Grid -->
<div class="competitions-grid">
    <!-- competition cards -->
</div>
```

---

## ⚖️ Discipline Specific

```html
<!-- Discipline Card -->
<div class="discipline-card">
    <div class="discipline-header">
        <h3 class="discipline-title">Incident Title</h3>
        <span class="discipline-severity high">High</span>
    </div>
    
    <div class="discipline-student-info">
        <div class="discipline-student-avatar">JS</div>
        <div class="discipline-student-details">
            <div class="discipline-student-name">John Smith</div>
            <div class="discipline-student-class">Grade 10A</div>
        </div>
    </div>
    
    <div class="discipline-description">
        <div class="discipline-description-title">Incident</div>
        <p class="discipline-description-text">Description...</p>
    </div>
    
    <div class="discipline-action">
        <div class="discipline-action-title">Action Taken</div>
        <p class="discipline-action-text">Action...</p>
    </div>
    
    <span class="discipline-status resolved">Resolved</span>
</div>

<!-- Severity Levels -->
<span class="discipline-severity low">Low</span>
<span class="discipline-severity medium">Medium</span>
<span class="discipline-severity high">High</span>

<!-- Status -->
<span class="discipline-status resolved">Resolved</span>
<span class="discipline-status pending">Pending</span>
<span class="discipline-status escalated">Escalated</span>
```

---

## 📊 Dashboard Specific

```html
<!-- Stat Card -->
<div class="dashboard-stat-card">
    <div class="dashboard-stat-header">
        <div class="dashboard-stat-icon primary">
            <span class="material-icons-round">group</span>
        </div>
    </div>
    <div class="dashboard-stat-title">Total Members</div>
    <div class="dashboard-stat-value">150</div>
    <div class="dashboard-stat-change positive">+12%</div>
</div>

<!-- Activity Item -->
<div class="dashboard-activity-list">
    <div class="dashboard-activity-item">
        <div class="dashboard-activity-icon" style="background: #dcfce7;">
            <span class="material-icons-round">event</span>
        </div>
        <div class="dashboard-activity-content">
            <div class="dashboard-activity-title">Activity Title</div>
            <div class="dashboard-activity-time">2 hours ago</div>
        </div>
    </div>
</div>

<!-- Quick Action -->
<div class="dashboard-quick-actions">
    <a href="#" class="dashboard-quick-action">
        <span class="dashboard-quick-action-icon material-icons-round">add</span>
        <span class="dashboard-quick-action-label">New Item</span>
    </a>
</div>
```

---

## 🎯 Common Patterns

### Card with Header and Actions:
```html
<div class="card">
    <div class="card-header">
        <div>
            <h2 class="card-title">Title</h2>
            <p class="card-subtitle">Subtitle</p>
        </div>
        <span class="badge badge-success">Active</span>
    </div>
    <div>Content</div>
    <div style="display: flex; gap: 0.5rem; margin-top: 1rem;">
        <button class="btn btn-primary">Save</button>
        <button class="btn btn-secondary">Cancel</button>
    </div>
</div>
```

### Form with Icon Input:
```html
<div class="form-group">
    <label class="form-label">Email</label>
    <div style="position: relative;">
        <span class="material-icons-round" style="position: absolute; left: 0.75rem; top: 50%; transform: translateY(-50%); color: #9ca3af;">
            email
        </span>
        <input type="email" class="form-input" style="padding-left: 2.5rem;">
    </div>
</div>
```

### Grid Layout:
```html
<!-- Auto-fit responsive grid -->
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
    <div class="card">Card 1</div>
    <div class="card">Card 2</div>
    <div class="card">Card 3</div>
</div>
```

---

