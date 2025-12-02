#!/bin/bash
set -e

echo "🚀 Setting up FastAPI Backend..."

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    exit 1
fi

# Create venv
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
source venv/bin/activate

# Install dependencies
echo "⬇️  Installing dependencies..."
pip install -r requirements.txt

# Create .env if missing
if [ ! -f ".env" ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
fi

# Verify database connection
echo "🔌 Verifying database connection..."
if python scripts/verify_db_connection.py; then
    VERIFIED=true
else
    VERIFIED=false
fi

# Run migrations (if alembic is set up)
if [ -f "alembic.ini" ]; then
    if [ "$VERIFIED" = false ]; then
        echo "🔄 Running migrations..."
        alembic upgrade head
    else
        echo "⏭️  Skipping migrations (schema already present)"
    fi
fi

echo "✅ Backend setup complete!"
