#!/bin/bash
set -e

echo "🏁 Starting Complete CRM Backend Setup..."

# Parse arguments
SKIP_DB=false

for arg in "$@"
do
    case $arg in
        --skip-db)
        SKIP_DB=true
        shift
        ;;
    esac
done

# 1. Database Setup
if [ "$SKIP_DB" = false ]; then
    echo ""
    echo "----------------------------------------"
    echo "📦 Step 1: Database Setup"
    echo "----------------------------------------"
    chmod +x database/setup.sh
    ./database/setup.sh
else
    echo "⏭️  Skipping database setup..."
fi

# 2. Backend Setup
echo ""
echo "----------------------------------------"
echo "🐍 Step 2: Backend Environment Setup"
echo "----------------------------------------"
chmod +x scripts/setup_backend.sh
./scripts/setup_backend.sh

# 3. Ensure Admin User on fresh setup
if [ "$SKIP_DB" = false ]; then
    echo ""
    echo "----------------------------------------"
    echo "👤 Step 3: Ensuring Admin User"
    echo "----------------------------------------"
    source venv/bin/activate
    python scripts/create_admin.py
fi

# 4. Final Verification
echo ""
echo "----------------------------------------"
echo "🔍 Step 4: Final Verification"
echo "----------------------------------------"
source venv/bin/activate
python scripts/verify_setup.py

echo ""
echo "🎉 Setup Complete! You can now run the server with:"
echo "   source venv/bin/activate"
echo "   uvicorn app.main:app --reload"
