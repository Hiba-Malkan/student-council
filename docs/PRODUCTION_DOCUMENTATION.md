# Production Deployment Guide

This document covers deploying the Student Council Management System to a production server running Ubuntu 20.04 LTS or later, with PostgreSQL, Redis, Nginx, and Gunicorn.

## Pre-Deployment Checklist

**Application**
- All tests pass: `python manage.py test`
- `DEBUG=False` in `.env`
- `SECRET_KEY` is random and at least 50 characters
- All production environment variables are configured
- Code is reviewed and committed
- Migrations are tested locally
- Static files are collected locally

**Infrastructure**
- Server is provisioned and accessible (Ubuntu 20.04 LTS or later recommended)
- PostgreSQL database is created
- Redis is running
- Email service is configured (SendGrid, AWS SES, or SMTP)
- SSL/TLS certificates are available (Let's Encrypt)
- Domain DNS is configured
- Firewall rules are defined
- Load balancer is configured, if applicable

Document the deployment process, rollback procedure, on-call contact, and incident response plan before deploying.

## Server Setup

For 100-500 concurrent users, provision 4 CPU cores, 16GB RAM, 100GB SSD, and 100+ Mbps bandwidth.

```bash
sudo apt update && sudo apt upgrade -y

sudo apt install -y \
  python3.13 \
  python3-pip \
  python3-venv \
  postgresql \
  postgresql-contrib \
  redis-server \
  nginx \
  git \
  supervisor \
  certbot \
  python3-certbot-nginx
```

Create a dedicated application user:

```bash
sudo useradd -m -s /bin/bash appuser
sudo usermod -aG sudo appuser

sudo mkdir -p /var/www/student-council
sudo chown -R appuser:appuser /var/www/student-council
```

## Application Deployment

```bash
su - appuser

cd /var/www/student-council
git clone https://github.com/Hiba-Malkan/student-council.git .

python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r backend/requirements.txt
pip install gunicorn
```

Create the database and user:

```bash
sudo -u postgres psql

CREATE DATABASE student_council_db;
CREATE USER appuser WITH PASSWORD 'strong_password_here';
ALTER ROLE appuser SET client_encoding TO 'utf8';
ALTER ROLE appuser SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE student_council_db TO appuser;
\q
```

Run migrations:

```bash
cd /var/www/student-council/backend
source ../venv/bin/activate

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy
```

### Configuring roles in production

The superuser account created above has administrative access but no council role assigned. Role assignment requires a C-Suite role to exist first, so the initial setup must be done either through the Django admin at `https://yourdomain.com/admin/` (superusers can manage roles directly) or via the shell:

```bash
python manage.py shell
```

```python
from accounts.models import Role

student = Role.objects.create(name='Student', is_normal_student=True)
captain = Role.objects.create(name='Captain', can_manage_competitions=True)
class_rep = Role.objects.create(name='Class Rep')
president = Role.objects.create(
    name='President',
    can_edit_duty_roster=True,
    can_schedule_meetings=True,
    can_create_announcements=True,
    can_edit_announcements=True,
    can_view_discipline=True,
    can_manage_competitions=True,
    can_manage_gatepass=True,
)

from accounts.models import User
user = User.objects.get(username='yourusername')
user.role = president
user.save()

exit()
```

Once a C-Suite user exists, further role assignment can go through the API or the admin panel.

## Configuration

`backend/.env`:

```env
SECRET_KEY=your-super-secret-key-minimum-50-chars-random-string
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com
ENVIRONMENT=production

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_council_db
DB_USER=appuser
DB_PASSWORD=strong_password_here
DB_HOST=localhost
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=sg.your_sendgrid_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=server@yourdomain.com

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

SITE_URL=https://yourdomain.com
SITE_NAME=Student Council Management
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_SECURE=True
CSRF_COOKIE_HTTPONLY=True

SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True

LOG_LEVEL=INFO
LOG_FILE=/var/log/student-council/django.log
```

`gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8000"
backlog = 2048
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

accesslog = "/var/log/student-council/gunicorn_access.log"
errorlog = "/var/log/student-council/gunicorn_error.log"
loglevel = "info"

proc_name = "student-council"
daemon = False
user = "appuser"
group = "appuser"
```

`/etc/nginx/sites-available/student-council`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/student-council/frontend/static/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/student-council/backend/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/student-council /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Security Hardening

```bash
sudo certbot certonly --webroot -w /var/www/student-council/frontend -d yourdomain.com -d www.yourdomain.com

sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
sudo certbot renew --dry-run
```

```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw default deny incoming
sudo ufw status
```

Secure PostgreSQL by setting authentication to `scram-sha-256` and enabling SSL in `pg_hba.conf` and `postgresql.conf`.

Secure Redis by setting a password and disabling destructive commands in `redis.conf`:

```
requirepass your_strong_redis_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""
```

```bash
sudo systemctl restart redis-server
```

Confirm in `settings.py`: `DEBUG` is `False`, `ALLOWED_HOSTS` is set correctly, `SECRET_KEY` is strong and random, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `SECURE_BROWSER_XSS_FILTER` are all `True`, and `SECURE_HSTS_SECONDS` is `31536000`.

## Signup Management in Production

`/competitions/signups/` and `/clubs/signups/` require a C-Suite role. Users without President, Vice President, Secretary, or Treasurer status receive a `403 Forbidden` on these pages.

Signup deletion is protected server-side as well:

```
DELETE /api/competitions/{id}/delete_signup/?signup_id={signup_id}    Requires C-Suite role
DELETE /api/clubs/{id}/delete_signup/?signup_id={signup_id}           Requires C-Suite role
```

Both require a valid JWT in the Authorization header. Monitor `/var/log/student-council/django.log` for `403 Forbidden` (permission denied), `404 Not Found` (missing signup or resource), and `500 Internal Server Error` (database or server fault) responses on these endpoints.

## Monitoring and Logging

```bash
sudo mkdir -p /var/log/student-council
sudo chown -R appuser:appuser /var/log/student-council
```

Configure Django's `LOGGING` setting in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/student-council/django.log',
            'maxBytes': 1024*1024*100,  # 100MB
            'backupCount': 10,
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
```

DEBUG-level messages contain development detail and should not appear in production logs. INFO covers normal operation, WARNING flags issues that don't stop the system, ERROR indicates a failure affecting functionality, and CRITICAL requires immediate attention.

| Metric | Target | Alert threshold |
|---|---|---|
| CPU usage | Below 70% | 85% |
| Memory usage | Below 80% | 90% |
| Disk usage | Below 80% | 85% |
| Response time | Below 200ms | 500ms |
| Error rate | Below 1% | 5% |
| Database connections | Below 80 | 100 |
| Celery queue length | Below 100 | 1000 |

**Note:** The target and alert values above reflect two slightly different threshold sets that existed across the original documentation — the celery queue alert in particular varied between 500 and 1000 in earlier drafts. 1000 is used here as the alert threshold; adjust to match your actual queue throughput once you have production traffic data.

When a metric crosses its alert threshold, check the logs first to see what changed. For database issues, check connection counts and running queries. For memory issues, identify the largest processes before deciding whether to restart. For response time issues, run `EXPLAIN ANALYZE` on the slow query before adding an index — guessing at which column needs an index usually wastes more time than it saves.

## Backup and Disaster Recovery

`/usr/local/bin/backup-student-council.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/student-council"
DB_NAME="student_council_db"
DB_USER="appuser"
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

pg_dump -U $DB_USER $DB_NAME | gzip > $BACKUP_DIR/db_$(date +%Y%m%d_%H%M%S).sql.gz
tar -czf $BACKUP_DIR/media_$(date +%Y%m%d_%H%M%S).tar.gz /var/www/student-council/backend/media/

aws s3 cp $BACKUP_DIR/ s3://your-backup-bucket/daily/ --recursive

find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
```

```bash
sudo chmod +x /usr/local/bin/backup-student-council.sh
sudo crontab -e
# 0 2 * * * /usr/local/bin/backup-student-council.sh
```

**Recovery procedure**

1. `sudo systemctl stop gunicorn`
2. `psql -U appuser -d student_council_db < backup.sql`
3. Restore media: `tar -xzf media_backup.tar.gz`
4. `python manage.py migrate`
5. `sudo systemctl start gunicorn`
6. Verify: `curl https://yourdomain.com/api/clubs/`

Recovery Time Objective: 30 minutes. Recovery Point Objective: 24 hours. Daily backups are retained for 30 days, weekly backups for 3 months, and monthly backups indefinitely.

## Scaling and Performance

For horizontal scaling, place multiple application servers behind a load balancer (AWS ELB/ALB), with shared PostgreSQL (AWS RDS) and Redis (AWS ElastiCache), and S3 for static and media files.

```sql
CREATE INDEX idx_user_username ON accounts_user(username);
CREATE INDEX idx_club_status ON clubs_club(status);
CREATE INDEX idx_duty_user ON duty_roster_duty(assigned_to_id);
CREATE INDEX idx_duty_status ON duty_roster_duty(is_completed);

ANALYZE accounts_user;
ANALYZE clubs_club;
```

```bash
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET tcp-backlog 511
```

## Process Management

`/etc/supervisor/conf.d/student-council.conf`:

```ini
[program:student-council-gunicorn]
command=/var/www/student-council/venv/bin/gunicorn \
    --config /var/www/student-council/gunicorn_config.py \
    student_council.wsgi:application
directory=/var/www/student-council/backend
user=appuser
autostart=true
autorestart=true
stdout_logfile=/var/log/student-council/gunicorn.log

[program:student-council-celery-worker]
command=/var/www/student-council/venv/bin/celery \
    -A student_council worker --loglevel=info
directory=/var/www/student-council/backend
user=appuser
autostart=true
autorestart=true
stdout_logfile=/var/log/student-council/celery_worker.log

[group:student-council]
programs=student-council-gunicorn,student-council-celery-worker
```

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

**Note:** Celery Beat is not included in this Supervisor config. If scheduled notifications are required in production, add a corresponding `[program:student-council-celery-beat]` block running `celery -A student_council beat --loglevel=info`.

## Maintenance Schedule

### Daily

Check that all services are running and review logs for errors.

```bash
tail -f /var/log/student-council/django.log
celery -A student_council inspect active
psql -c "SELECT count(*) FROM pg_stat_activity;"

systemctl status gunicorn
systemctl status celery-worker
systemctl status celery-beat
systemctl status redis-server
systemctl status postgresql
```

Watch for `ERROR` and `WARNING` entries, not just crashes — a service can be technically "up" and still be failing requests.

### Weekly

Optimize the database and verify backups are actually restorable, not just present.

```bash
vacuumdb -U postgres student_council_db

psql -U postgres student_council_db -c "
  SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
  FROM pg_tables
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

pg_dump -U postgres student_council_db | gzip > /backups/db_$(date +%Y%m%d).sql.gz

grep ERROR /var/log/student-council/*.log
grep WARNING /var/log/student-council/*.log
```

### Monthly

Clean up old data, update dependencies, and check for slow queries before they become a production incident.

```bash
# Remove notifications older than 6 months
python manage.py shell << EOF
from django.utils import timezone
from datetime import timedelta
from notifications.models import Notification

old_date = timezone.now() - timedelta(days=180)
Notification.objects.filter(created_at__lt=old_date).delete()
EOF

pip install --upgrade -r requirements.txt
pip-audit

apt update && apt upgrade -y

# Find slow queries
psql -c "SELECT query, calls, mean_time FROM pg_stat_statements
         ORDER BY mean_time DESC LIMIT 10;"

# Review index usage
psql -c "SELECT schemaname, tablename, indexname
         FROM pg_indexes
         WHERE schemaname NOT IN ('pg_catalog', 'information_schema');"
```

`pip-audit` flags known CVEs in installed dependencies. Running it monthly, even when nothing has broken, catches vulnerable packages before they become an incident.

## Troubleshooting

**Application won't start** — check Supervisor status, review `/var/log/student-council/gunicorn.log`, run `python manage.py check --deploy`, and test Gunicorn directly.

**Database connections fail** — verify PostgreSQL is running, test with `psql`, check database size, check connection limits.

**Celery tasks not processing** — check worker status and logs, verify Redis is running, restart the worker or purge stuck tasks.

**High memory usage** — identify the consuming process, check for caching or query issues, restart the affected service.

**SSL certificate expired** — `sudo certbot certificates`, `sudo certbot renew`, `sudo certbot renew --dry-run` to verify.

## Rollback

```bash
sudo supervisorctl stop all
cd /var/www/student-council
git revert HEAD
source venv/bin/activate
pip install -r backend/requirements.txt
python backend/manage.py migrate
sudo supervisorctl start all
curl https://yourdomain.com/api/clubs/
```

## Production Readiness Checklist

- Security hardening complete
- SSL/TLS configured
- Automated backups running
- Monitoring and alerting configured
- Load testing complete
- Disaster recovery tested
- Team trained on procedures
- Documentation reviewed
- Contact information current
- Incident response plan exists

---

**Document Version:** 1.0
**Last Updated:** July 2026