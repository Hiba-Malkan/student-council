import logging
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db.models import Q
from django.utils.html import strip_tags
from django.utils import timezone

from accounts.models import User

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared CSS / layout helpers
# ---------------------------------------------------------------------------

_BASE_STYLES = """
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;color:#33312c;line-height:1.6;margin:0;padding:0;background:#f4f4f2;}
.wrap{max-width:600px;margin:0 auto;}
.card{background:#ffffff;border:1px solid #e7e4dd;border-radius:8px;overflow:hidden;}
.header{padding:26px 32px 22px;color:#fff;}
.header h1{margin:0;font-size:21px;font-weight:700;line-height:1.25;color:#fff;}
.header .sub{margin:6px 0 0;font-size:13px;opacity:.85;}
.body{padding:26px 32px 30px;background:#ffffff;}
.body p{margin:0 0 15px;font-size:15px;}
.detail-box{margin:20px 0;}
.detail-box .row{padding:9px 0;border-bottom:1px solid #efede6;}
.detail-box .row:last-child{border-bottom:none;}
.detail-box .label{display:inline-block;min-width:140px;font-weight:600;font-size:14px;}
.btn{display:inline-block;padding:12px 26px;color:#fff !important;text-decoration:none;border-radius:5px;font-weight:600;font-size:14px;margin-top:4px;}
.footer{padding:16px 32px 20px;background:#faf9f6;border-top:1px solid #ece9e0;text-align:center;font-size:11px;color:#a19b8c;}
"""


def _html_email(header_color, icon, heading, subheading, body_html, btn_url, btn_text, btn_color=None):
    """Wrap content in a consistent branded email shell."""
    btn_color = btn_color or header_color
    icon_span = f'<span style="margin-right:6px;">{icon}</span>' if icon else ''
    sub = f'<div class="sub">{subheading}</div>' if subheading else ''
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><style>{_BASE_STYLES}</style></head>
<body>
  <div class="wrap">
    <div class="card">
      <div class="header" style="background:{header_color};">
        <h1>{icon_span}{heading}</h1>
        {sub}
      </div>
      <div class="body">
        {body_html}
        {f'<p style="text-align:center;"><a href="{btn_url}" class="btn" style="background:{btn_color};">{btn_text}</a></p>' if btn_url and btn_text else ''}
      </div>
      <div class="footer">Student Council &middot; Automated notice</div>
    </div>
  </div>
</body>
</html>"""


def _detail_box(color, rows):
    """Render a detail list. rows = list of (label, value) tuples."""
    inner = "".join(
        f'<div class="row"><span class="label" style="color:{color};">{lbl}:</span> {val}</div>'
        for lbl, val in rows
    )
    return f'<div class="detail-box">{inner}</div>'


def _emails(users):
    """Extract email addresses from a queryset / list of User objects."""
    return [u.email for u in users]


def discipline_alert_recipients():
    """Active phase heads and superusers — the people who action discipline alerts."""
    return User.objects.filter(
        Q(is_phase_head=True) | Q(is_superuser=True),
        is_active=True,
    ).distinct()


def _send(subject, html, recipients):
    """Low-level send helper.

    recipients can be a single email string or an iterable of email strings.
    Every recipient receives IDENTICAL content: recipients are chunked into
    groups of MASS_EMAIL_BATCH_SIZE (default 50) and each group is sent as one
    message with the group in BCC, so addresses stay private and we stay under
    provider per-message recipient limits.
    """
    if isinstance(recipients, str):
        recipients = [recipients]
    recipients = list(dict.fromkeys(r for r in recipients if r))  # dedupe, preserve order
    if not recipients:
        return False
    batch_size = getattr(settings, 'MASS_EMAIL_BATCH_SIZE', 50)
    fallback_from = settings.DEFAULT_FROM_EMAIL or 'noreply@localhost'
    try:
        for start in range(0, len(recipients), batch_size):
            batch = recipients[start:start + batch_size]
            if len(batch) == 1:
                to, bcc = batch, []
            else:
                to, bcc = [fallback_from], batch
            msg = EmailMultiAlternatives(
                subject=subject,
                body=strip_tags(html),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=to,
                bcc=bcc,
            )
            msg.attach_alternative(html, "text/html")
            msg.send()
        return True
    except Exception as e:
        logger.error(f"Email send failed to {recipients}: {e}", exc_info=True)
        return False


# ===========================================================================
# 1. MEETING SCHEDULED  (new meeting created)
# ===========================================================================
def send_meeting_scheduled_email(meeting, recipients):
    """
    meeting  – Meeting instance
    recipients – queryset / list of User objects

    One identical email is BCC'd to all recipients in batches (see `_send`).
    """
    COLOR = "#2d7a4f"
    rows = [
        ("Title",    meeting.title),
        ("Date",     meeting.date.strftime("%B %d, %Y")),
        ("Time",     getattr(meeting, 'time', None) or "TBD"),
        ("Location", meeting.location or "TBD"),
    ]
    if getattr(meeting, 'description', None):
        rows.append(("Details", meeting.description[:200]))
    body = (
        "<p>A new meeting has been scheduled. Please mark your calendar:</p>"
        + _detail_box(COLOR, rows)
        + "<p>Please make sure to arrive on time and come prepared.</p>"
    )
    html = _html_email(COLOR, "📅", "Meeting Scheduled", meeting.date.strftime("%B %d, %Y"),
                       body, f"{getattr(settings,'SITE_URL','')}/meetings/",
                       "View Meeting Details")
    _send(f"📅 Meeting Scheduled: {meeting.title}", html, _emails(recipients))


# ===========================================================================
# 2. MEETING TODAY  (morning reminder)
# ===========================================================================
def send_meeting_today_email(meeting, recipients):
    COLOR = "#1565c0"
    rows = [
        ("Meeting",  meeting.title),
        ("Time",     getattr(meeting, 'time', None) or "TBD"),
        ("Location", meeting.location or "TBD"),
    ]
    body = (
        "<p>Just a reminder — you have a meeting <strong>today</strong>:</p>"
        + _detail_box(COLOR, rows)
        + "<p>Please come prepared and be on time.</p>"
    )
    html = _html_email(COLOR, "📅", "Meeting Today", "Don't forget!",
                       body, f"{getattr(settings,'SITE_URL','')}/meetings/",
                       "View Meeting Details")
    _send(f"📅 Meeting Today: {meeting.title}", html, _emails(recipients))


# ===========================================================================
# 3. MEETING CANCELLED
# ===========================================================================
def send_meeting_cancelled_email(meeting, recipients):
    COLOR = "#8a1c1c"
    rows = [
        ("Meeting",  meeting.title),
        ("Was on",   meeting.date.strftime("%B %d, %Y")),
        ("Location", meeting.location or "TBD"),
    ]
    if getattr(meeting, 'cancellation_reason', None):
        rows.append(("Reason", meeting.cancellation_reason))
    body = (
        "<p>We want to let you know that the following meeting has been <strong>cancelled</strong>:</p>"
        + _detail_box(COLOR, rows)
        + "<p>We apologise for any inconvenience. You will be notified when it is rescheduled.</p>"
    )
    html = _html_email(COLOR, "❌", "Meeting Cancelled", meeting.date.strftime("%B %d, %Y"),
                       body, f"{getattr(settings,'SITE_URL','')}/meetings/", "View All Meetings")
    _send(f"❌ Meeting Cancelled: {meeting.title}", html, _emails(recipients))


# ===========================================================================
# 4. DUTY TODAY  (daily reminder for assigned member)
# ===========================================================================
def send_duty_today_email(duty):
    """duty – Duty instance with assigned_to populated."""
    COLOR = "#1565c0"
    user = duty.assigned_to
    location = duty.location or "TBD"
    subsidiary = duty.subsidiary_area if getattr(duty, 'subsidiary_area', None) else None
    rows = [
        ("Duty Type", duty.duty_type_name),
        ("Date",      duty.date.strftime("%B %d, %Y")),
        ("Location",  location + (f", {subsidiary}" if subsidiary else "")),
    ]
    if getattr(duty, 'instructions', None):
        rows.append(("Instructions", duty.instructions))
    body = (
        f"<p>This is your duty reminder for <strong>today</strong>:</p>"
        + _detail_box(COLOR, rows)
        + "<p>Please fulfill your duty responsibly. Mark it complete once done.</p>"
    )
    html = _html_email(COLOR, "📋", "Duty Reminder", "You're on duty today!",
                       body, f"{getattr(settings,'SITE_URL','')}/duty-roster/", "View Duty Roster")
    _send(f"📋 Duty Today: {duty.duty_type_name}", html, user.email)


# ===========================================================================
# 5. NEW ANNOUNCEMENT  (regular)
# ===========================================================================
def send_announcement_new_email(announcement, recipients):
    COLOR = "#6a1b9a"
    rows = [
        ("Title",    announcement.title),
        ("Category", getattr(announcement, 'announcement_type', 'General')),
    ]
    if getattr(announcement, 'published_at', None):
        rows.append(("Posted", announcement.published_at.strftime("%B %d, %Y")))
    preview = (announcement.content or "")[:250]
    if len(announcement.content or "") > 250:
        preview += "…"
    body = (
        "<p>There's a new announcement from the Student Council:</p>"
        + _detail_box(COLOR, rows)
        + f'<p style="color:#555;">{preview}</p>'
        + "<p>Click below to read the full announcement.</p>"
    )
    html = _html_email(COLOR, "📢", "New Announcement", announcement.title,
                       body, f"{getattr(settings,'SITE_URL','')}/announcements/", "Read Announcement")
    _send(f"📢 New Announcement: {announcement.title}", html, _emails(recipients))


# ===========================================================================
# 6. IMPORTANT / URGENT ANNOUNCEMENT
# ===========================================================================
def send_announcement_important_email(announcement, recipients):
    COLOR = "#8a1c1c"
    preview = (announcement.content or "")[:300]
    if len(announcement.content or "") > 300:
        preview += "…"
    body = (
        "<p>An <strong>urgent announcement</strong> requires your immediate attention:</p>"
        + _detail_box(COLOR, [("Subject", announcement.title)])
        + f'<div style="background:#fff3f3;border-radius:6px;padding:16px;margin:12px 0;color:#333;">{preview}</div>'
        + "<p>Please read the full announcement right away.</p>"
    )
    html = _html_email(COLOR, "🚨", "URGENT Announcement", "Immediate attention required",
                       body, f"{getattr(settings,'SITE_URL','')}/announcements/",
                       "View Urgent Announcement")
    _send(f"🚨 URGENT: {announcement.title}", html, _emails(recipients))


# ===========================================================================
# 7. NEW COMPETITION
# ===========================================================================
def send_competition_new_email(competition, recipients):
    COLOR = "#e65100"
    rows = [
        ("Competition", competition.name),
        ("Hosted by",   competition.hosted_by or "TBD"),
        ("Event Date",  competition.event_date.strftime("%B %d, %Y") if competition.event_date else "TBD"),
    ]
    if getattr(competition, 'deadline', None):
        rows.append(("Sign-up Deadline", competition.deadline.strftime("%B %d, %Y")))
    body = (
        "<p>A new competition has just been announced — don't miss it!</p>"
        + _detail_box(COLOR, rows)
        + "<p>Check it out and sign up before spots fill up!</p>"
    )
    html = _html_email(COLOR, "🏆", "New Competition", competition.name,
                       body, f"{getattr(settings,'SITE_URL','')}/competitions/", "View Competition")
    _send(f"🏆 New Competition: {competition.name}", html, _emails(recipients))


# ===========================================================================
# 8. COMPETITION DEADLINE SOON
# ===========================================================================
def send_competition_deadline_email(competition, days_remaining, recipients):
    COLOR = "#8a1c1c"
    deadline_str = competition.event_date.strftime("%B %d, %Y") if competition.event_date else "TBD"
    rows = [
        ("Competition",     competition.name),
        ("Days Remaining",  f"⏳ {days_remaining} day{'s' if days_remaining != 1 else ''}"),
        ("Deadline",        deadline_str),
    ]
    body = (
        "<p>Time is running out! The deadline for a competition is approaching fast:</p>"
        + _detail_box(COLOR, rows)
        + "<p>Make sure to submit before the deadline. Don't leave it to the last minute!</p>"
    )
    html = _html_email(COLOR, "⏰", "Competition Deadline Soon",
                       f"{days_remaining} day{'s' if days_remaining != 1 else ''} left",
                       body, f"{getattr(settings,'SITE_URL','')}/competitions/", "View & Sign Up")
    _send(f"⏰ Deadline Soon — {competition.name} ({days_remaining}d left)", html, _emails(recipients))


# ===========================================================================
# 9. DISCIPLINE WARNING  (3+ offenses — to phase heads & superusers)
# ===========================================================================
def send_discipline_warning_email(record, offense_log):
    """
    record      – DisciplineRecord instance
    offense_log – the triggering OffenseLog

    NOTE: This is not called automatically anymore (no per-offense emails).
    The only discipline email is the daily report to phase heads. Kept here so
    it can be used manually if needed.
    """
    COLOR = "#8a1c1c"
    recipients = discipline_alert_recipients()
    if not recipients.exists():
        return

    rows = [
        ("Student",        record.student_name),
        ("Class / Section", record.class_section),
        ("D.No",           record.dno),
        ("Total Offenses", f'<span style="color:{COLOR};font-weight:700;">{record.offense_count}</span>'),
        ("Latest Offense", offense_log.get_category_display()),
    ]
    if offense_log.reason:
        rows.append(("Reason", offense_log.reason))

    for st in recipients:
        body = (
            f"<p>A student has reached <strong>{record.offense_count} offenses</strong> and requires your attention:</p>"
            + _detail_box(COLOR, rows)
            + "<p>Please review the student's discipline record and take appropriate action.</p>"
        )
        html = _html_email(COLOR, "⚠️", "Discipline Alert",
                           f"{record.student_name} — {record.offense_count} offenses",
                           body, f"{getattr(settings,'SITE_URL','')}/discipline/detail/{record.id}/",
                           "View Discipline Record")
        _send(f"⚠️ Discipline Alert: {record.student_name} ({record.offense_count} offenses)", html, st.email)


# ===========================================================================
# 10. DAILY DISCIPLINE SUMMARY  (to phase heads & superusers only)
# ===========================================================================
def send_daily_discipline_report(students_qs, report_date):
    """
    students_qs – queryset of DisciplineRecord objects with 3+ offenses that had activity on report_date
    report_date – date object
    """
    COLOR = "#8a1c1c"
    recipients = discipline_alert_recipients()
    if not recipients.exists():
        return

    # Build report rows
    report_rows = []
    for record in students_qs:
        latest = record.offense_logs.filter(
            created_at__date=report_date
        ).order_by('-created_at').first()
        report_rows.append({
            'name':     record.student_name,
            'class':    record.class_section,
            'dno':      record.dno,
            'count':    record.offense_count,
            'category': latest.get_category_display() if latest else "—",
            'reason':   (latest.reason or "No reason provided") if latest else "—",
        })

    if not report_rows:
        return

    # Build table rows HTML
    table_rows_html = "".join(f"""
        <tr style="background:{'#fff8f8' if i % 2 == 0 else '#fff'};">
          <td style="padding:10px 12px;border:1px solid #e0e0e0;">{r['name']}</td>
          <td style="padding:10px 12px;border:1px solid #e0e0e0;">{r['class']}</td>
          <td style="padding:10px 12px;border:1px solid #e0e0e0;">{r['dno']}</td>
          <td style="padding:10px 12px;border:1px solid #e0e0e0;text-align:center;font-weight:700;color:{COLOR};">{r['count']}</td>
          <td style="padding:10px 12px;border:1px solid #e0e0e0;">{r['category']}<br><small style="color:#777;">{r['reason']}</small></td>
        </tr>""" for i, r in enumerate(report_rows))

    table_html = f"""
    <table style="width:100%;border-collapse:collapse;margin:20px 0;font-size:14px;">
      <thead>
        <tr style="background:#f5f5f5;">
          <th style="padding:11px 12px;border:1px solid #ddd;text-align:left;">Student Name</th>
          <th style="padding:11px 12px;border:1px solid #ddd;text-align:left;">Class</th>
          <th style="padding:11px 12px;border:1px solid #ddd;text-align:left;">D.No</th>
          <th style="padding:11px 12px;border:1px solid #ddd;text-align:center;">Offenses</th>
          <th style="padding:11px 12px;border:1px solid #ddd;text-align:left;">Latest Offense</th>
        </tr>
      </thead>
      <tbody>{table_rows_html}</tbody>
    </table>"""

    date_str = report_date.strftime("%B %d, %Y")

    for st in recipients:
        body = (
            f"<p>Here is the daily discipline summary for <strong>{date_str}</strong>. "
            f"The students listed below reached 3 or more offenses:</p>"
            + table_html
            + f"<p><strong>Total students requiring attention: {len(report_rows)}</strong></p>"
            + "<p>Please review their records and coordinate necessary follow-up.</p>"
        )
        html = _html_email(COLOR, "📊", "Daily Discipline Report", date_str,
                           body, f"{getattr(settings,'SITE_URL','')}/discipline/", "View All Records")
        _send(f"📊 Daily Discipline Report — {date_str}", html, st.email)


# ===========================================================================
# Generic notification email dispatcher  (used by send_pending_email_notifications task)
# ===========================================================================
def send_notification_email(notification):
    """Route a Notification object to the correct typed sender, or fall back to generic."""
    if not notification.send_email or notification.email_sent:
        return False

    try:
        _dispatch_notification_email(notification)
        notification.email_sent = True
        notification.email_sent_at = timezone.now()
        notification.save(update_fields=['email_sent', 'email_sent_at'])
        return True
    except Exception as e:
        logger.error(f"send_notification_email failed for #{notification.id}: {e}", exc_info=True)
        return False


def _dispatch_notification_email(notification):
    """Build and send email from a persisted Notification object."""
    nt = notification.notification_type
    recipient = notification.recipient
    title = notification.title
    message = notification.message
    action_url = f"{getattr(settings, 'SITE_URL', '')}{notification.action_url}" if notification.action_url else "#"

    COLOR_MAP = {
        'MEETING_TODAY':            "#1565c0",
        'MEETING_MORNING':          "#1565c0",
        'MEETING_10MIN':            "#1565c0",
        'MEETING_RESCHEDULED':      "#0277bd",
        'MEETING_CANCELLED':        "#8a1c1c",
        'DUTY_TODAY':               "#1565c0",
        'DUTY_ASSIGNED':            "#1565c0",
        'DUTY_MORNING':             "#1565c0",
        'ANNOUNCEMENT_NEW':         "#6a1b9a",
        'ANNOUNCEMENT_IMPORTANT':   "#8a1c1c",
        'COMPETITION_NEW':          "#e65100",
        'COMPETITION_DEADLINE':     "#8a1c1c",
        'COMPETITION_STARTING':     "#8a1c1c",
        'DISCIPLINE_WARNING':       "#8a1c1c",
        'DISCIPLINE_DAILY_REPORT':  "#8a1c1c",
        'DISCIPLINE_NEW_OFFENSE':   "#8a1c1c",
    }
    color = COLOR_MAP.get(nt, "#2d7a4f")

    body = (
        f"<p>{message}</p>"
    )
    html = _html_email(color, "", title, "", body, action_url, "View Details")
    _send(title, html, recipient.email)


# ===========================================================================
# GATE PASS EMAILS  (lives in gatepass/utils.py but defined here for convenience;
#                    import from gatepass.tasks via gatepass.utils)
# ===========================================================================
def send_gatepass_submitted_email(gatepass):
    """
    Emails sent when a gate pass request is submitted:
      • The student
      • The parent (parent_email)
      • All CTs (ct_email — stored as comma-separated or single address)
      • All phase heads
    """
    COLOR = "#1565c0"
    rows = [
        ("Student",         gatepass.name),
        ("D.No",            gatepass.dno),
        ("Class",           f"{gatepass.student_class} – {gatepass.student_section}"),
        ("Date Requested",  str(gatepass.requested_date)),
        ("Reason",          gatepass.reason or "Not provided"),
        ("Status",          "⏳ Pending Review"),
    ]

    def _gatepass_body():
        return (
            f"<p>A gate pass request has been <strong>submitted</strong> and is awaiting approval.</p>"
            + _detail_box(COLOR, rows)
        )

    # 1. Student
    if gatepass.student and gatepass.student.email:
        body = _gatepass_body()
        body += "<p>You will be notified once a decision has been made.</p>"
        html = _html_email(COLOR, "📝", "Gate Pass Submitted", "Your request is under review",
                           body, None, None)
        _send("📝 Gate Pass Request Submitted", html, gatepass.student.email)

    # 2. Parent
    if gatepass.parent_email:
        body = (
            f"<p>A gate pass has been requested for your child. Details are below:</p>"
            + _detail_box(COLOR, rows)
            + "<p>You will be notified when the request has been reviewed.</p>"
        )
        html = _html_email(COLOR, "📝", "Gate Pass Request", f"Submitted for {gatepass.name}",
                           body, None, None)
        _send(f"📝 Gate Pass Request — {gatepass.name}", html, gatepass.parent_email)

    # 3. CT(s) — ct_email can be comma-separated
    ct_emails = [e.strip() for e in (gatepass.ct_email or "").split(",") if e.strip()]
    for ct_email in ct_emails:
        body = (
            f"<p>A gate pass request has been submitted for one of your students:</p>"
            + _detail_box(COLOR, rows)
            + f"<p>Please review in the system if follow-up is needed.</p>"
        )
        html = _html_email(COLOR, "📝", "Gate Pass Request", f"Student: {gatepass.name}",
                           body, f"{getattr(settings,'SITE_URL','')}/gatepass/",
                           "View Gate Pass")
        _send(f"📝 Gate Pass Request — {gatepass.name}", html, ct_email)

    # 4. Phase heads
    phase_heads = User.objects.filter(is_phase_head=True, is_active=True)
    for ph in phase_heads:
        body = (
            f"<p>A new gate pass request has been submitted for your phase:</p>"
            + _detail_box(COLOR, rows)
            + "<p>Please review and ensure it is handled appropriately.</p>"
        )
        html = _html_email(COLOR, "📝", "Gate Pass Request", f"Student: {gatepass.name}",
                           body, f"{getattr(settings,'SITE_URL','')}/gatepass/",
                           "View Gate Pass")
        _send(f"📝 Gate Pass Request — {gatepass.name}", html, ph.email)


def send_gatepass_decision_email(gatepass):
    """
    Emails sent when a gate pass is approved or denied:
      • The student
      • The parent
      • All CTs
    """
    is_approved = gatepass.status == "approved"
    COLOR = "#2e7d32" if is_approved else "#8a1c1c"
    icon = "✅" if is_approved else "❌"
    decision_label = "Approved" if is_approved else "Denied"
    decision_word = "approved" if is_approved else "denied"

    rows = [
        ("Student",         gatepass.name),
        ("D.No",            gatepass.dno),
        ("Class",           f"{gatepass.student_class} – {gatepass.student_section}"),
        ("Date Requested",  str(gatepass.requested_date)),
        ("Decision",        f'<strong style="color:{COLOR};">{decision_label}</strong>'),
    ]
    if gatepass.approved_by:
        rows.append(("Reviewed by", gatepass.approved_by.get_full_name() or gatepass.approved_by.username))
    if gatepass.approval_note:
        rows.append(("Note", gatepass.approval_note))
    if gatepass.approval_timestamp:
        rows.append(("Decision Time", gatepass.approval_timestamp.strftime("%B %d, %Y – %H:%M")))

    def _decision_body(extra_note=""):
        return (
            f"<p>The gate pass request for <strong>{gatepass.name}</strong> has been "
            f"<strong style='color:{COLOR};'>{decision_word}</strong>.</p>"
            + _detail_box(COLOR, rows)
            + (f"<p>{extra_note}</p>" if extra_note else "")
        )

    # 1. Student
    if gatepass.student and gatepass.student.email:
        extra = (
            "You may proceed with the gate pass."
            if is_approved else
            "If you have questions, please speak to your phase head."
        )
        body = _decision_body(extra)
        html = _html_email(COLOR, icon, f"Gate Pass {decision_label}",
                           "Your request has been reviewed", body, None, None)
        _send(f"{icon} Gate Pass {decision_label}", html, gatepass.student.email)

    # 2. Parent
    if gatepass.parent_email:
        body = _decision_body(
            "Please contact the school if you have any concerns."
        )
        html = _html_email(COLOR, icon, f"Gate Pass {decision_label}",
                           f"Request for {gatepass.name}", body, None, None)
        _send(f"{icon} Gate Pass {decision_label} — {gatepass.name}", html, gatepass.parent_email)

    # 3. CT(s)
    ct_emails = [e.strip() for e in (gatepass.ct_email or "").split(",") if e.strip()]
    for ct_email in ct_emails:
        body = _decision_body()
        html = _html_email(COLOR, icon, f"Gate Pass {decision_label}",
                           f"Student: {gatepass.name}", body,
                           f"{getattr(settings,'SITE_URL','')}/gatepass/",
                           "View Gate Pass")
        _send(f"{icon} Gate Pass {decision_label} — {gatepass.name}", html, ct_email)