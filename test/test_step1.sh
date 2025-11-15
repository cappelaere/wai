#!/bin/bash
# Test script to run Step 1 for 2 applications

# Change to project root directory (parent of test/)
cd "$(dirname "$0")/.." || exit 1

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file (step1.py will use INPUT_DATA_DIR automatically)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run Step 1 with limit of 2 applications
# step1.py will automatically use INPUT_DATA_DIR from .env to construct the path
python code/step1.py --limit 138

