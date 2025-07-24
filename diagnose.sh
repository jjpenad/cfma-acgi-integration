#!/bin/bash

# CFMA Service Diagnostic Script
echo "🔍 Diagnosing CFMA service issues..."

# Check if we're in the right directory
echo "📁 Current directory: $(pwd)"
echo "📁 Directory contents:"
ls -la

# Check if virtual environment exists
echo "🐍 Checking virtual environment..."
if [ -d "venv" ]; then
    echo "✅ Virtual environment exists"
    echo "📁 Virtual environment contents:"
    ls -la venv/bin/ | head -10
else
    echo "❌ Virtual environment not found"
    exit 1
fi

# Check if gunicorn is installed
echo "🔧 Checking gunicorn installation..."
if [ -f "venv/bin/gunicorn" ]; then
    echo "✅ Gunicorn found"
    echo "📋 Gunicorn version:"
    venv/bin/gunicorn --version
else
    echo "❌ Gunicorn not found in virtual environment"
    echo "📦 Installing gunicorn..."
    source venv/bin/activate
    pip install gunicorn
fi

# Check if the app module exists
echo "📦 Checking app module..."
if [ -f "src/app.py" ]; then
    echo "✅ src/app.py exists"
else
    echo "❌ src/app.py not found"
    echo "📁 src/ directory contents:"
    ls -la src/
fi

# Test the app manually
echo "🧪 Testing app manually..."
source venv/bin/activate
export FLASK_ENV=production
export FLASK_APP=wsgi:app

echo "📋 Testing imports..."
python3 -c "
try:
    from src.app import app
    print('✅ App import successful')
except Exception as e:
    print(f'❌ App import failed: {e}')
    import traceback
    traceback.print_exc()
"

echo "📋 Testing database..."
python3 -c "
try:
    from src.models import init_db, create_default_admin
    print('✅ Database models import successful')
except Exception as e:
    print(f'❌ Database models import failed: {e}')
    import traceback
    traceback.print_exc()
"

# Test gunicorn manually
echo "🚀 Testing gunicorn manually..."
timeout 10s venv/bin/gunicorn --workers 1 --bind 127.0.0.1:5001 --timeout 30 wsgi:app &
GUNICORN_PID=$!
sleep 3

if kill -0 $GUNICORN_PID 2>/dev/null; then
    echo "✅ Gunicorn started successfully"
    echo "🧪 Testing health endpoint..."
    sleep 2
    curl -s http://127.0.0.1:5001/health || echo "❌ Health endpoint failed"
    kill $GUNICORN_PID
else
    echo "❌ Gunicorn failed to start"
fi

# Check systemd logs
echo "📋 Recent systemd logs for cfma service:"
sudo journalctl -u cfma -n 20 --no-pager

# Check if port 5000 is in use
echo "🔌 Checking port 5000:"
sudo netstat -tlnp | grep :5000 || echo "Port 5000 is not in use"

# Check file permissions
echo "🔐 Checking file permissions:"
ls -la venv/bin/gunicorn
ls -la src/app.py

echo "🔍 Diagnosis complete!" 