#!/bin/bash
# Test script to run Step 4 to combine reports and generate PDF

# Change to project root directory (parent of test/)
cd "$(dirname "$0")/.." || exit 1

# Activate virtual environment
source venv/bin/activate

# Load environment variables from .env file (step4.py will use OUTPUT_DATA_DIR automatically)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run Step 4 to combine all reports and generate PDF
# step4.py will automatically use OUTPUT_DATA_DIR from .env to find report files
python code/step4.py --scholarship-folder "Delaney_Wings" --limit 20

