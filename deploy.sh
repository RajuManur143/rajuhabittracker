#!/bin/bash
# Production deployment script for Habit Tracker

set -e  # Exit on error

echo "🚀 Starting Habit Tracker deployment..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Check environment variables
echo "⚙️  Checking environment variables..."
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  WARNING: SECRET_KEY not set. Generating a new one..."
    export SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "Generated SECRET_KEY: $SECRET_KEY"
fi

export FLASK_ENV=production

# Initialize database
echo "🗄️  Initializing database..."
python3 -c "from appraju import init_db; init_db()"

# Start the application
echo "🎯 Starting application with Gunicorn..."
gunicorn -w 4 -b 0.0.0.0:${PORT:-5000} --timeout 120 appraju:app

echo "✨ Deployment complete!"
