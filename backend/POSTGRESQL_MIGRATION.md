# PostgreSQL Migration Guide (psycopg3)

This guide will help you migrate from SQLite to PostgreSQL using psycopg-binary 3.3.2.

## Prerequisites

1. **Install PostgreSQL** on your system:
   - **macOS**: `brew install postgresql@15`
   - **Ubuntu/Debian**: `sudo apt-get install postgresql postgresql-contrib`
   - **Windows**: Download from https://www.postgresql.org/download/

2. **Start PostgreSQL service**:
   - **macOS**: `brew services start postgresql@15`
   - **Ubuntu/Debian**: `sudo systemctl start postgresql`
   - **Windows**: PostgreSQL service should start automatically

## Step 1: Create PostgreSQL Database

Open PostgreSQL command line:

```bash
# On macOS/Linux
psql postgres

# Or connect as postgres user
sudo -u postgres psql
```

Then create the database and user:

```sql
-- Create database
CREATE DATABASE student_council_db;

-- Create user (optional, you can use the default postgres user)
CREATE USER council_admin WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE student_council_db TO council_admin;

-- Exit
\q
```

## Step 2: Install Python PostgreSQL Adapter

```bash
cd backend
pip install -r requirements.txt
```

This will install `psycopg-binary==3.3.2` (psycopg3), which is the modern PostgreSQL adapter for Python.

**Note:** psycopg3 is faster and more efficient than psycopg2. It works seamlessly with Django 4.2+.

## Step 3: Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
cp .env.example .env
```

Edit `.env` and update the database settings:

```env
# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_council_db
DB_USER=postgres  # or council_admin if you created a custom user
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432

# Set to False to use PostgreSQL
USE_SQLITE=False
```

## Step 4: Export Data from SQLite (Optional - if you have existing data)

If you have existing data in SQLite that you want to keep:

```bash
# Export data from SQLite
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission > datadump.json
```

## Step 5: Run Migrations on PostgreSQL

```bash
# Make sure PostgreSQL is configured in .env
python manage.py migrate
```

## Step 6: Import Data (Optional - if you exported data)

If you exported data in Step 4:

```bash
python manage.py loaddata datadump.json
```

## Step 7: Create Superuser

If you're starting fresh or didn't export data:

```bash
python manage.py createsuperuser
```

## Step 8: Test the Setup

```bash
# Run the development server
python manage.py runserver

# In another terminal, test the database connection
python manage.py dbshell
```

## Troubleshooting

### Connection Refused

If you get "connection refused" errors:

1. Check PostgreSQL is running:
   ```bash
   # macOS
   brew services list | grep postgresql
   
   # Linux
   sudo systemctl status postgresql
   ```

2. Check PostgreSQL is listening on the correct port:
   ```bash
   psql -U postgres -h localhost -p 5432 -l
   ```

### Authentication Failed

If you get authentication errors:

1. Check your username and password in `.env`
2. Try resetting the password:
   ```bash
   psql postgres
   ALTER USER postgres WITH PASSWORD 'new_password';
   ```

### Database Does Not Exist

If you get "database does not exist":

```bash
psql postgres
CREATE DATABASE student_council_db;
\q
```

## Switching Back to SQLite (Development Only)

If you want to switch back to SQLite for development:

1. Update `.env`:
   ```env
   USE_SQLITE=True
   ```

2. Run migrations:
   ```bash
   python manage.py migrate
   ```

## Production Deployment

For production, consider using:
- **Managed PostgreSQL**: AWS RDS, DigitalOcean Managed Databases, Heroku Postgres
- **Environment-specific settings**: Use different `.env` files for development and production
- **Database backups**: Set up regular automated backups
- **SSL connections**: Enable SSL for database connections in production

## Performance Tips

After migration, you may want to:

1. **Create indexes** for frequently queried fields
2. **Optimize queries** using `select_related()` and `prefetch_related()`
3. **Enable connection pooling** using `django-db-pool` or `pgbouncer`
4. **Monitor performance** with tools like `django-debug-toolbar`

## Additional Resources

- Django PostgreSQL Documentation: https://docs.djangoproject.com/en/4.2/ref/databases/#postgresql-notes
- PostgreSQL Official Docs: https://www.postgresql.org/docs/
