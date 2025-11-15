#!/bin/bash
# Test script to run Step 2 for 2 applications

# Change to project root directory (parent of test/)
cd "$(dirname "$0")/.." || exit 1

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file (step2.py will use OUTPUT_DATA_DIR automatically)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run Step 2 with limit of X applications for Delaney_Wings scholarship
# step2.py will automatically use OUTPUT_DATA_DIR from .env to find output folders
python code/step2.py --scholarship-folder "Delaney_Wings" --limit 138

