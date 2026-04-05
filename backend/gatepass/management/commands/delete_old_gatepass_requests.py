from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from gatepass.models import GatePass

class Command(BaseCommand):
    help = 'Deletes gate pass requests older than 30 days.'

    def handle(self, *args, **kwargs):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Filter for approved or denied requests older than 30 days
        old_requests = GatePass.objects.filter(
            status__in=['approved', 'denied'],
            updated_at__lt=thirty_days_ago
        )
        
        count = old_requests.count()
        
        if count > 0:
            old_requests.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} old gate pass requests.'))
        else:
            self.stdout.write(self.style.SUCCESS('No old gate pass requests to delete.'))
