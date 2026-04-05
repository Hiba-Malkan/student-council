from celery import shared_task
from django.core.mail import send_mail
from .models import GatePass
from accounts.models import User, Role

@shared_task
def send_gate_pass_submission_email(gatepass_id):
    """
    Sends notification emails when a new gate pass is submitted.
    """
    try:
        gatepass = GatePass.objects.get(id=gatepass_id)
        student = gatepass.student

        # Build common email message
        email_message = (
            f"A gate pass request has been submitted for {gatepass.name} "
            f"({gatepass.student_class} - {gatepass.student_section}).\n\n"
            f"D.No: {gatepass.dno}\n"
            f"Requested Date: {gatepass.requested_date}\n"
            f"Reason: {gatepass.reason}"
        )

        # 1. Send email to student
        send_mail(
            subject='Gate Pass Request Submitted',
            message=f"Your gate pass request has been submitted.\n\n" + email_message,
            from_email='noreply@studentcouncil.com',
            recipient_list=[student.email],
            fail_silently=False
        )
        
        # 2. Send email to parent and class teacher
        recipient_list = [gatepass.parent_email]
        if gatepass.ct_email:
            recipient_list.append(gatepass.ct_email)

        send_mail(
            subject='Gate Pass Request Submission',
            message=email_message,
            from_email='noreply@studentcouncil.com',
            recipient_list=recipient_list,
            fail_silently=False
        )
        
        # 3. Send email to gate pass managers
        manager_roles = Role.objects.filter(can_manage_gatepass=True)
        managers = User.objects.filter(role__in=manager_roles)
        manager_emails = [m.email for m in managers if m.email]
        
        if manager_emails:
            send_mail(
                subject='New Gate Pass Request',
                message=f'New gate pass request from {gatepass.name}.\n\n' + email_message,
                from_email='noreply@studentcouncil.com',
                recipient_list=manager_emails,
                fail_silently=False
            )
        return f"Submission emails sent for GatePass ID: {gatepass_id}"
    except GatePass.DoesNotExist:
        return f"GatePass with id {gatepass_id} does not exist."
    except Exception as e:
        # Log the error for debugging
        print(f"Failed to send submission emails for GatePass ID {gatepass_id}: {e}")
        # Optionally re-raise to have the task retried
        raise

@shared_task
def send_gate_pass_decision_email(gatepass_id):
    """
    Sends an email notification to the student, parent, and class teacher
    about the decision on a gate pass request.
    """
    try:
        gatepass = GatePass.objects.get(id=gatepass_id)
    except GatePass.DoesNotExist:
        return "GatePass not found."

    status_text = 'Approved' if gatepass.status == 'approved' else 'Denied'
    
    message = (
        f"The gate pass request for {gatepass.name} on {gatepass.requested_date.strftime('%B %d, %Y')} "
        f"has been {status_text.lower()}.\n\n"
    )
    if gatepass.approval_note:
        message += f"Note from manager: {gatepass.approval_note}\n\n"
    
    message += f"Details:\n"
    message += f"D.No: {gatepass.dno}\n"
    message += f"Reason: {gatepass.reason}"

    # Build recipient list
    recipient_list = [gatepass.student.email, gatepass.parent_email]
    if gatepass.ct_email:
        recipient_list.append(gatepass.ct_email)
    
    # Remove any empty email addresses
    recipient_list = [email for email in recipient_list if email]

    if not recipient_list:
        return "No recipients found."

    send_mail(
        subject=f'Gate Pass Request {status_text}',
        message=message,
        from_email='noreply@studentcouncil.com',
        recipient_list=recipient_list,
        fail_silently=False 
    )
    
    return f"Decision email sent for GatePass ID: {gatepass_id}"
