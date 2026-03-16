#!/bin/bash

# Comprehensive test script for voice chatbot
# Tests all scenarios with both servers running

echo "=========================================="
echo "Voice Chatbot Comprehensive Test Suite"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Django server is running
echo -e "${YELLOW}Checking if Django server is running...${NC}"
if curl -s http://localhost:8000/admin/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Django server is running${NC}"
else
    echo -e "${RED}❌ Django server is not running${NC}"
    echo "Please start Django server: python manage.py runserver"
    exit 1
fi

# Check if Redis is running (optional)
echo -e "${YELLOW}Checking Redis...${NC}"
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Redis is running${NC}"
else
    echo -e "${YELLOW}⚠️  Redis is not running (using InMemoryChannelLayer)${NC}"
fi

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py makemigrations
python manage.py migrate

# Create test user if needed
echo -e "${YELLOW}Creating test user...${NC}"
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='testuser').exists():
    User.objects.create_user('testuser', 'test@example.com', 'testpass123')
    print("Test user created")
else:
    print("Test user already exists")
EOF

# Run unit tests
echo -e "${YELLOW}Running unit tests...${NC}"
python manage.py test tests.test_security tests.test_database -v 2

# Run integration tests
echo -e "${YELLOW}Running integration tests...${NC}"
python manage.py test tests.test_integration -v 2

# Run manual WebSocket tests
echo -e "${YELLOW}Running manual WebSocket tests...${NC}"
python tests/test_manual.py

echo ""
echo -e "${GREEN}=========================================="
echo "All tests completed!"
echo "==========================================${NC}"

