from django.test import TestCase
from rest_framework.test import APIClient

from accounts.models import Role, User
from .models import DeletionLog, DisciplineRecord, OffenseLog


class DisciplineApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.manager = User.objects.create_user(
            'manager', 'manager@example.com', 'password123',
            is_staff=True,
            role=Role.objects.create(name='Discipline', can_record_discipline=True, can_view_discipline=True),
        )
        self.viewer = User.objects.create_user(
            'viewer', 'viewer@example.com', 'password123',
            role=Role.objects.create(name='Viewer', can_view_discipline=True),
        )

    def test_create_normalizes_dno_and_creates_initial_offense_log(self):
        self.client.force_authenticate(self.manager)
        response = self.client.post('/api/discipline/records/', {
            'student_name': 'Alex', 'class_section': '10A', 'dno': 'D1234', 'offense_count': 1,
            'category': 'LATE', 'reason': 'Late to class',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        record = DisciplineRecord.objects.get()
        self.assertEqual(record.dno, 'D1234')
        self.assertEqual(record.created_by, self.manager)
        self.assertEqual(record.offense_logs.get().category, 'LATE')

    def test_increasing_count_adds_log_and_deleting_logs_keeps_count_correct(self):
        record = DisciplineRecord.objects.create(student_name='Alex', class_section='10A', dno='D1234', offense_count=1, created_by=self.manager)
        first = OffenseLog.objects.create(record=record, category='LATE')
        self.client.force_authenticate(self.manager)
        response = self.client.patch(f'/api/discipline/records/{record.id}/', {
            'offense_count': 2, 'category': 'BEHAVIOR', 'reason': 'Disruptive',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(record.offense_logs.count(), 2)
        newest = record.offense_logs.exclude(id=first.id).get()
        self.assertEqual(self.client.delete(f'/api/discipline/offense-logs/{newest.id}/').status_code, 204)
        record.refresh_from_db()
        self.assertEqual(record.offense_count, 1)
        self.assertEqual(self.client.delete(f'/api/discipline/offense-logs/{first.id}/').status_code, 204)
        self.assertFalse(DisciplineRecord.objects.filter(id=record.id).exists())

    def test_viewer_can_read_but_not_write_and_dno_validation_rejects_bad_format(self):
        DisciplineRecord.objects.create(student_name='Alex', class_section='10A', dno='D1234')
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get('/api/discipline/records/').status_code, 200)
        self.assertEqual(self.client.post('/api/discipline/records/', {
            'student_name': 'Bad', 'class_section': '10A', 'dno': 'D9999',
        }, format='json').status_code, 403)
        self.client.force_authenticate(self.manager)
        response = self.client.post('/api/discipline/records/', {
            'student_name': 'Bad', 'class_section': '10A', 'dno': 'bad',
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('dno', response.data)


class DeletionLogTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(
            'manager', 'manager@example.com', 'password123',
            is_staff=True,
            role=Role.objects.create(name='Discipline', can_record_discipline=True, can_view_discipline=True),
        )
        self.record = DisciplineRecord.objects.create(
            student_name='Alex', class_section='10A', dno='D1234', offense_count=1, created_by=self.manager,
        )

    def test_deleting_offense_log_records_snapshot(self):
        log = OffenseLog.objects.create(record=self.record, category='LATE', reason='Late to class')
        log.delete()
        entry = DeletionLog.objects.get(object_type='OFFENSE')
        self.assertEqual(entry.dno, 'D1234')
        self.assertEqual(entry.student_name, 'Alex')
        self.assertEqual(entry.category, 'LATE')
        self.assertEqual(entry.reason, 'Late to class')

    def test_deleting_record_records_snapshot(self):
        self.record.delete()
        entry = DeletionLog.objects.get(object_type='RECORD')
        self.assertEqual(entry.dno, 'D1234')
        self.assertEqual(entry.offense_count, 1)

    def test_api_delete_captures_deleted_by(self):
        log = OffenseLog.objects.create(record=self.record, category='LATE')
        client = APIClient()
        client.force_authenticate(self.manager)
        response = client.delete(f'/api/discipline/offense-logs/{log.id}/')
        self.assertEqual(response.status_code, 204)
        entry = DeletionLog.objects.get(object_type='OFFENSE')
        self.assertEqual(entry.deleted_by, self.manager)
