from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from accounts.models import User


def send_notification_email(notification):
    """Send email for a notification"""
    if not notification.send_email or notification.email_sent:
        return
    
    try:
        subject = notification.title
        html_message = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2d7a4f;">{notification.title}</h2>
                    <p>{notification.message}</p>
                    {f'<p><a href="{settings.SITE_URL}{notification.action_url}" style="display: inline-block; padding: 10px 20px; background-color: #2d7a4f; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px;">View Details</a></p>' if notification.action_url else ''}
                    <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                    <p style="font-size: 12px; color: #666;">
                        This is an automated notification from Student Council Management System.
                    </p>
                </div>
            </body>
        </html>
        """
        plain_message = strip_tags(html_message)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[notification.recipient.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        notification.email_sent = True
        notification.email_sent_at = timezone.now()
        notification.save()
        
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send email to {notification.recipient.email}: {str(e)}", exc_info=True)
        return False


def send_daily_discipline_report(students, date):
    """Send daily report of students with 3+ offenses to phase heads"""
    from django.utils import timezone
    
    phase_heads = User.objects.filter(is_phase_head=True)
    
    if not phase_heads.exists():
        return
    
    # Prepare report data
    report_lines = []
    for student in students:
        latest_log = student.offense_logs.filter(created_at__date=date).latest('created_at')
        report_lines.append({
            'name': student.student_name,
            'class': student.class_section,
            'dno': student.dno,
            'total_offenses': student.offense_count,
            'latest_category': latest_log.get_category_display(),
            'latest_reason': latest_log.reason or 'No reason provided'
        })
    
    # Create HTML email
    html_message = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 800px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #d32f2f;">Daily Discipline Report - {date.strftime("%B %d, %Y")}</h2>
                <p>The following students reached 3 or more offenses on {date.strftime("%B %d, %Y")}:</p>
                
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #f5f5f5;">
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Student Name</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Class</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">D.No</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: center;">Total Offenses</th>
                            <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Latest Offense</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''
                        <tr>
                            <td style="border: 1px solid #ddd; padding: 12px;">{student['name']}</td>
                            <td style="border: 1px solid #ddd; padding: 12px;">{student['class']}</td>
                            <td style="border: 1px solid #ddd; padding: 12px;">{student['dno']}</td>
                            <td style="border: 1px solid #ddd; padding: 12px; text-align: center; font-weight: bold; color: #d32f2f;">{student['total_offenses']}</td>
                            <td style="border: 1px solid #ddd; padding: 12px;">{student['latest_category']}<br><small style="color: #666;">{student['latest_reason']}</small></td>
                        </tr>
                        ''' for student in report_lines])}
                    </tbody>
                </table>
                
                <p style="margin-top: 20px;">Total students requiring attention: <strong>{len(report_lines)}</strong></p>
                
                <hr style="margin: 20px 0; border: none; border-top: 1px solid #ddd;">
                <p style="font-size: 12px; color: #666;">
                    This is an automated daily report from the Student Council Management System.
                </p>
            </div>
        </body>
    </html>
    """
    
    plain_message = f"""
Daily Discipline Report - {date.strftime("%B %d, %Y")}

The following students reached 3 or more offenses on {date.strftime("%B %d, %Y")}:

"""
    for student in report_lines:
        plain_message += f"\n{student['name']} ({student['class']}, {student['dno']}) - {student['total_offenses']} offenses"
        plain_message += f"\nLatest: {student['latest_category']} - {student['latest_reason']}\n"
    
    plain_message += f"\nTotal students requiring attention: {len(report_lines)}"
    
    # Send to all phase heads
    for phase_head in phase_heads:
        try:
            email = EmailMultiAlternatives(
                subject=f'Daily Discipline Report - {date.strftime("%B %d, %Y")}',
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[phase_head.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send discipline report to {phase_head.email}: {str(e)}", exc_info=True)
