#!/bin/bash
# Test script to run Step 3 for 2 applications

# Change to project root directory (parent of test/)
cd "$(dirname "$0")/.." || exit 1

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file (step3.py will use OUTPUT_DATA_DIR automatically)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run Step 3 with limit of X applications for Delaney_Wings scholarship
# step3.py will automatically use OUTPUT_DATA_DIR from .env to find output folders
python code/step3.py --scholarship-folder "Delaney_Wings" --limit 0

