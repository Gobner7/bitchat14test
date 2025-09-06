#!/bin/bash

echo "CSFloat Auto-Flipper Quick Start"
echo "================================"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your CSFLOAT_API_KEY"
    echo "Press Enter after adding your API key..."
    read
fi

# Install dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt

# Create directories
mkdir -p logs data models

# Check services
echo ""
echo "Checking services..."

# MongoDB
if pgrep -x "mongod" > /dev/null; then
    echo "✓ MongoDB is running"
else
    echo "⚠️  MongoDB is not running"
    echo "Start MongoDB with: mongod --dbpath /path/to/data"
fi

# Redis
if pgrep -x "redis-server" > /dev/null; then
    echo "✓ Redis is running"
else
    echo "⚠️  Redis is not running"
    echo "Start Redis with: redis-server"
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start the bot:"
echo "  python3 main.py"
echo ""
echo "For dry run mode:"
echo "  python3 main.py --dry-run"
echo ""
echo "Monitor at: http://localhost:9090/dashboard"