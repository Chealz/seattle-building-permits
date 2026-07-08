#!/bin/bash
# One-shot setup: creates a virtualenv, installs deps, runs the app.
set -e
cd "$(dirname "$0")"

# Find the newest Python 3.10+ available
PY=""
for candidate in python3.14 python3.13 python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PY="$candidate"
        break
    fi
done

if [ -z "$PY" ]; then
    echo "❌ No Python 3.10+ found."
    echo "   Your system Python 3.9 is end-of-life. Install Python 3.13 from:"
    echo "   https://www.python.org/downloads/"
    echo "   Then run this script again:  bash setup.sh"
    exit 1
fi

echo "✅ Using $PY ($($PY --version))"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    "$PY" -m venv .venv
fi

source .venv/bin/activate
echo "Installing packages..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo "✅ Setup complete. Launching app..."
streamlit run app.py
