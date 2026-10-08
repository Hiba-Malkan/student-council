from django.db.models.signals import post_delete
from django.dispatch import receiver

from .audit import get_current_user
from .models import DeletionLog, DisciplineRecord, OffenseLog


def _record_deletion(instance, object_type):
    if object_type == 'RECORD':
        return DeletionLog.objects.create(
            object_type=object_type,
            dno=instance.dno,
            student_name=instance.student_name,
            class_section=instance.class_section,
            offense_count=instance.offense_count,
            deleted_by=get_current_user(),
        )

    record = instance.record
    return DeletionLog.objects.create(
        object_type=object_type,
        dno=record.dno if record else '',
        student_name=record.student_name if record else '',
        class_section=record.class_section if record else '',
        category=instance.category,
        reason=instance.reason,
        deleted_by=get_current_user(),
    )


@receiver(post_delete, sender=DisciplineRecord)
def log_discipline_record_delete(sender, instance, **kwargs):
    _record_deletion(instance, 'RECORD')


@receiver(post_delete, sender=OffenseLog)
def log_offense_log_delete(sender, instance, **kwargs):
    _record_deletion(instance, 'OFFENSE')