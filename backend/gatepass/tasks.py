from celery import shared_task
from django.conf import settings


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_gate_pass_submission_email(self, gatepass_id):
    try:
        from gatepass.models import GatePass
        from notifications.utils import send_gatepass_submitted_email
        gatepass = GatePass.objects.select_related('student', 'approved_by').get(id=gatepass_id)
        send_gatepass_submitted_email(gatepass)
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_gate_pass_decision_email(self, gatepass_id):
    try:
        from gatepass.models import GatePass
        from notifications.utils import send_gatepass_decision_email
        gatepass = GatePass.objects.select_related('student', 'approved_by').get(id=gatepass_id)
        send_gatepass_decision_email(gatepass)
    except Exception as exc:
        raise self.retry(exc=exc)