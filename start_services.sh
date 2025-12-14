#!/bin/bash

# Student Council App - Service Starter
# This script starts all required services for the app

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   Starting Student Council Management System Services    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Redis is running
echo "Checking Redis..."
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Redis is already running"
else
    echo -e "${YELLOW}⚠${NC} Starting Redis..."
    brew services start redis
    sleep 2
    if redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Redis started successfully"
    else
        echo -e "${RED}✗${NC} Failed to start Redis"
        echo "  Run: brew install redis"
        exit 1
    fi
fi

echo ""
echo "Opening terminals for services..."
echo ""

# Start Django Server
echo "1. Starting Django server (http://localhost:8000)..."
osascript -e 'tell app "Terminal" 
    do script "cd /Users/hiba/student-council/backend && echo \"Starting Django Server...\" && python manage.py runserver"
end tell'

sleep 1

# Start Celery Worker
echo "2. Starting Celery worker (for background tasks)..."
osascript -e 'tell app "Terminal" 
    do script "cd /Users/hiba/student-council/backend && echo \"Starting Celery Worker...\" && celery -A student_council worker --loglevel=info"
end tell'

sleep 1

# Start Celery Beat
echo "3. Starting Celery Beat (for scheduled notifications)..."
osascript -e 'tell app "Terminal" 
    do script "cd /Users/hiba/student-council/backend && echo \"Starting Celery Beat...\" && celery -A student_council beat --loglevel=info"
end tell'

echo ""
echo -e "${GREEN}✓${NC} All services started in separate terminal windows!"
echo ""
echo "Services running:"
echo "  • Django Server:  http://localhost:8000"
echo "  • Celery Worker:  Processing background tasks"
echo "  • Celery Beat:    Scheduled notifications (7 AM, 4 PM, etc.)"
echo "  • Redis:          Message broker"
echo ""
echo "To stop services:"
echo "  • Close the terminal windows"
echo "  • Or press Ctrl+C in each terminal"
echo ""
echo "To check if emails are configured:"
echo "  python check_email_setup.py"
echo ""
