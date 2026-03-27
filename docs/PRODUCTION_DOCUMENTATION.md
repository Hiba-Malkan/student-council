# Student Council Management System — Production Deployment Guide

Deploy this application to a production server running Ubuntu 20.04 LTS or later with PostgreSQL, Redis, Nginx, and Gunicorn.

Before deploying to production, verify:

- All tests pass with `python manage.py test`
- DEBUG is set to False in `.env`
- SECRET_KEY is random and at least 50 characters long
- All environment variables are configured for production
- Code has been reviewed and committed to Git
- Database migrations have been tested locally
- Static files have been collected locally

Ensure infrastructure is ready:

- Server is provisioned and accessible (recommend Ubuntu 20.04 LTS)
- PostgreSQL database is created
- Redis cluster is running
- Email service is configured (SendGrid, AWS SES, or SMTP)
- SSL/TLS certificates are obtained (use Let's Encrypt)
- Domain name is configured with DNS
- Firewall rules are set up
- Load balancer is configured if needed

Document the deployment process, rollback procedures, on-call contact information, and incident response procedures before deployment.

## Server Setup

For 100-500 concurrent users, provision a server with 4 CPU cores, 16GB RAM, 100GB SSD storage, and 100+ Mbps bandwidth. Use Ubuntu 20.04 LTS or later as the operating system.

Update the system and install required packages:

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

Create a dedicated user account for the application:

```bash
sudo useradd -m -s /bin/bash appuser
sudo usermod -aG sudo appuser

sudo mkdir -p /var/www/student-council
sudo chown -R appuser:appuser /var/www/student-council
```

## Application Deployment

Switch to the application user and clone the repository:

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

Create the PostgreSQL database and user:

```bash
sudo -u postgres psql

CREATE DATABASE student_council_db;
CREATE USER appuser WITH PASSWORD 'strong_password_here';
ALTER ROLE appuser SET client_encoding TO 'utf8';
ALTER ROLE appuser SET default_transaction_isolation TO 'read committed';
GRANT ALL PRIVILEGES ON DATABASE student_council_db TO appuser;
\q
```

Run database migrations:

```bash
cd /var/www/student-council/backend
source ../venv/bin/activate

python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
python manage.py check --deploy
```

After initial setup, create the required roles in production. Your superuser account has administrative access but needs a role assigned. The system supports five role types: Student (default for all new users), Captain, Class Representative, and C-Suite roles (President, Vice President, Secretary, Treasurer).

To set up roles in production, use the Django admin panel at `https://yourdomain.com/admin/`. Only superusers can create and manage roles initially. Create the standard roles first, then assign a C-Suite role to your superuser account. Once a C-Suite user exists, they can assign roles to other users through the API or admin panel.

Alternatively, create roles via the shell:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from accounts.models import Role

# Create standard roles
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
    can_manage_competitions=True
)

# Assign President role to your superuser
from accounts.models import User
user = User.objects.get(username='yourusername')
user.role = president
user.save()

exit()
```

## Configuration

Create `backend/.env` with production settings:

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

Configure Gunicorn by creating `gunicorn_config.py`:

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

Configure Nginx at `/etc/nginx/sites-available/student-council`:

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

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/student-council /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Security Hardening

Obtain SSL/TLS certificates from Let's Encrypt using Certbot:

```bash
sudo certbot certonly --webroot -w /var/www/student-council/frontend -d yourdomain.com -d www.yourdomain.com

sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
sudo certbot renew --dry-run
```

Configure the firewall to allow only necessary ports:

```bash
sudo ufw enable
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw default deny incoming
sudo ufw status
```

Secure PostgreSQL by editing `/etc/postgresql/*/main/pg_hba.conf` and `/etc/postgresql/*/main/postgresql.conf`. Set authentication to md5 or scram-sha-256 and enable SSL.

Secure Redis by editing `/etc/redis/redis.conf` to set a password and disable dangerous commands:

```bash
requirepass your_strong_redis_password
rename-command FLUSHDB ""
rename-command FLUSHALL ""

sudo systemctl restart redis-server
```

Verify Django security settings in `settings.py`:

- DEBUG is False
- ALLOWED_HOSTS contains your domains
- SECRET_KEY is strong and random
- SECURE_SSL_REDIRECT is True
- SESSION_COOKIE_SECURE is True
- CSRF_COOKIE_SECURE is True
- SECURE_HSTS_SECONDS is 31536000
- SECURE_BROWSER_XSS_FILTER is True

## Signup Management in Production

In production, the signup management pages (`/competitions/signups/` and `/clubs/signups/`) require C-Suite role access. Only administrators with President, Vice President, Secretary, or Treasurer roles can view and manage signups. Students and other roles see a 403 Forbidden error when accessing these pages.

The pages display paginated lists of all signups for a selected competition or club. Administrators can remove signups using the delete action, which opens a confirmation modal asking the user to verify the removal.

The modal styling is designed for reliability across different browsers and environments. It uses a combination of inline styles for structural properties (padding, font sizing, borders) and Tailwind CSS classes for color variants that change with dark mode. This hybrid approach avoids CSS specificity issues and ensures the modal displays correctly under all conditions.

When monitoring production, watch for failed DELETE requests to the signup endpoints. Check the error logs for:
- 403 Forbidden errors indicating insufficient permissions
- 404 Not Found errors indicating the signup or resource doesn't exist
- 500 Internal Server errors indicating database or server issues

The signup deletion endpoints are protected by C-Suite role checks:
- `DELETE /api/competitions/{id}/delete_signup/?signup_id={signup_id}` — Requires C-Suite role
- `DELETE /api/clubs/{id}/delete_signup/?signup_id={signup_id}` — Requires C-Suite role

Both endpoints require authentication and appropriate admin permissions. Include your JWT token in the Authorization header for requests.

Check production logs at `/var/log/student-council/django.log` for signup deletion errors and permission denials.

## Monitoring & Logging

Create the log directory:

```bash
sudo mkdir -p /var/log/student-council
sudo chown -R appuser:appuser /var/log/student-council
```

Configure Django logging in `settings.py` to write to rotating file handlers. Set LOG_LEVEL to INFO in production. Log files rotate at 100MB with 10 backup files retained.

Monitor these key metrics: CPU usage (alert at 85%), memory usage (alert at 90%), disk usage (alert at 85%), response time (alert above 500ms), error rate (alert above 1%), database connections (alert above 80), and Celery queue length (alert above 1000).

## Backup & Disaster Recovery

Create an automated daily backup script at `/usr/local/bin/backup-student-council.sh`:

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

Schedule it in crontab:

```bash
sudo chmod +x /usr/local/bin/backup-student-council.sh
sudo crontab -e

# Add: 0 2 * * * /usr/local/bin/backup-student-council.sh
```

To recover from a backup:

1. Stop the application: `sudo systemctl stop gunicorn`
2. Drop and recreate the database
3. Restore the backup: `psql -U appuser -d student_council_db < backup.sql`
4. Restore media files: `tar -xzf media_backup.tar.gz`
5. Verify migrations: `python manage.py migrate`
6. Restart: `sudo systemctl start gunicorn`
7. Test: `curl https://yourdomain.com/api/clubs/`

The system targets a 30-minute Recovery Time Objective and 24-hour Recovery Point Objective.

## Scaling & Performance

For horizontal scaling, use a load balancer (AWS ELB/ALB) with multiple application servers. All servers connect to shared PostgreSQL (AWS RDS) and Redis (AWS ElastiCache) instances. S3 stores static files and media.

Optimize the database by creating indexes on frequently queried columns:

```sql
CREATE INDEX idx_user_username ON accounts_user(username);
CREATE INDEX idx_club_status ON clubs_club(status);
CREATE INDEX idx_duty_user ON duty_roster_duty(user_id);
CREATE INDEX idx_duty_status ON duty_roster_duty(status);

ANALYZE accounts_user;
ANALYZE clubs_club;
```

Optimize Redis for better performance:

```bash
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru
redis-cli CONFIG SET tcp-backlog 511
redis-cli INFO stats
```

## Maintenance Operations

Configure Supervisor to manage application services. Create `/etc/supervisor/conf.d/student-council.conf`:

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

Start services:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

Daily maintenance includes checking service status, reviewing logs, checking disk space, and verifying database health.

Weekly maintenance includes database cleanup (`vacuumdb`), analyzing statistics, checking disk usage, and reviewing error logs.

Monthly maintenance includes updating system packages, updating Python packages, checking for security vulnerabilities, cleaning old records, and creating offline backups.

## Troubleshooting

If the application won't start, check Supervisor status, view logs at `/var/log/student-council/gunicorn.log`, run `python manage.py check --deploy`, and test Gunicorn directly.

If database connections fail, verify PostgreSQL is running, test the connection with `psql`, check database size, and increase connection limits if needed.

If Celery tasks are not processing, check Celery worker status, view logs, verify Redis is running, and restart the worker or purge stuck tasks.

If memory usage is high, identify processes consuming memory, check Django settings for caching and database issues, and restart services.

If SSL certificates expire, check expiry with `sudo certbot certificates`, renew with `sudo certbot renew`, and test with `sudo certbot renew --dry-run`.

## Deployment Rollback

If deployment fails, revert to the previous commit:

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

## Production Readiness

Before deployment:

- All security hardening is complete
- SSL/TLS certificates are configured
- Automated backups are running
- Monitoring and alerting are configured
- Load testing is complete
- Disaster recovery is tested
- Team is trained
- Documentation is reviewed
- Contact information is updated
- Incident response plan exists

---

**Document Version:** 1.0  
**Last Updated:** March 26, 2026  
**Status:** Ready for Production