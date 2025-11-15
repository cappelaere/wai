#!/bin/bash

# Test script for step5.py - Generate Scholarship Statistics Report

# Change to project root
cd "$(dirname "$0")/.." || exit 1

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment
source venv/bin/activate

# Run step5.py
echo "Running step5.py to generate statistics report..."
echo ""

python code/step5.py \
    --scholarship-folder "Delaney_Wings"

echo ""
echo "Test completed!"

