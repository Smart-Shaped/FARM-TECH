#!/bin/bash

# Exit on any error
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Database is ready!"

# Create database if it doesn't exist (with better error handling)
echo "Creating database if it doesn't exist..."
export PGPASSWORD=$DB_PASSWORD

# Check if database exists and create if it doesn't
DB_EXISTS=$(psql -h $DB_HOST -U $DB_USER -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" 2>/dev/null || echo "0")

if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating database $DB_NAME..."
    psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || {
        echo "Database creation failed, but continuing..."
    }
else
    echo "Database $DB_NAME already exists."
fi

# Create static directory if it doesn't exist
echo "Creating static directories..."
mkdir -p static

# Create initial migrations for custom apps
echo "Creating initial migrations..."
python manage.py makemigrations users --noinput || echo "Users migrations already exist or failed"
python manage.py makemigrations core --noinput || echo "Core migrations already exist or failed"

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "Creating superuser if it doesn't exist..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
try:
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print('Superuser created successfully')
    else:
        print('Superuser already exists')
except Exception as e:
    print(f'Error creating superuser: {e}')
EOF

# Collect static files in production
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    echo "Collecting static files..."
    python manage.py collectstatic --noinput
fi

echo "Initialization completed successfully!"

# Execute the main command
exec "$@"