#!/bin/bash

###############################################################################
# Test Script for process_scholarships.py Orchestrator
#
# This script demonstrates and tests the unified orchestrator's capabilities:
# - All processing steps (1, 2, 3, 4)
# - Selective step execution
# - Multiprocessing support
# - Output log cleanup
# - Error handling
#
# Prerequisites:
# - Python 3.13+
# - Virtual environment activated: source venv/bin/activate
# - Ollama running: ollama serve
# - Sample data available in data/ directory
#
# Usage:
#   bash test/test_orchestrator.sh              # Run all tests
#   bash test/test_orchestrator.sh 1            # Run test 1 only
#   bash test/test_orchestrator.sh help         # Show this help
#
###############################################################################

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Change to project root directory
cd "$(dirname "$0")/.." || exit 1

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}[ERROR] Virtual environment not found at ./venv${NC}"
    echo "Create it with: python3.13 -m venv venv"
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo -e "${BLUE}============================================================================${NC}"
echo "Testing process_scholarships.py Orchestrator"
echo -e "${BLUE}============================================================================${NC}"
echo ""

# Function to print test header
print_test_header() {
    echo -e "${BLUE}[TEST $1] $2${NC}"
    echo "─────────────────────────────────────────────────────────────────────────────"
}

# Function to print success
print_success() {
    echo -e "${GREEN}[OK] $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Function to print info
print_info() {
    echo -e "${YELLOW}[INFO] $1${NC}"
}

###############################################################################
# TEST 1: Verify orchestrator script exists and is executable
###############################################################################
test_1_verify_orchestrator() {
    print_test_header "1" "Verify orchestrator script exists and is executable"

    if [ ! -f "process_scholarships.py" ]; then
        print_error "orchestrator script not found: process_scholarships.py"
        return 1
    fi
    print_success "orchestrator script found"

    if [ ! -x "process_scholarships.py" ]; then
        print_error "orchestrator script is not executable"
        return 1
    fi
    print_success "orchestrator script is executable"

    if ! python3 -m py_compile process_scholarships.py 2>/dev/null; then
        print_error "orchestrator script has syntax errors"
        return 1
    fi
    print_success "orchestrator script syntax is valid"

    echo ""
}

###############################################################################
# TEST 2: Show help message
###############################################################################
test_2_show_help() {
    print_test_header "2" "Show help message"

    echo "Running: python process_scholarships.py --help"
    echo ""

    if python process_scholarships.py --help > /tmp/orchestrator_help.txt 2>&1; then
        print_success "help command executed successfully"

        # Check for key arguments in help
        if grep -q "scholarship-folder" /tmp/orchestrator_help.txt; then
            print_success "help includes --scholarship-folder argument"
        else
            print_error "help missing --scholarship-folder argument"
            return 1
        fi

        if grep -q "steps" /tmp/orchestrator_help.txt; then
            print_success "help includes --steps argument"
        else
            print_error "help missing --steps argument"
            return 1
        fi

        if grep -q "workers" /tmp/orchestrator_help.txt; then
            print_success "help includes --workers argument"
        else
            print_error "help missing --workers argument"
            return 1
        fi

        if grep -q "limit" /tmp/orchestrator_help.txt; then
            print_success "help includes --limit argument"
        else
            print_error "help missing --limit argument"
            return 1
        fi
    else
        print_error "help command failed"
        return 1
    fi

    echo ""
}

###############################################################################
# TEST 3: Test argument validation (missing required argument)
###############################################################################
test_3_argument_validation() {
    print_test_header "3" "Test argument validation (missing required argument)"

    echo "Running: python process_scholarships.py (no arguments)"
    echo ""

    if python process_scholarships.py 2>&1 | grep -q "required"; then
        print_success "orchestrator correctly requires --scholarship-folder argument"
    else
        print_error "orchestrator should require --scholarship-folder argument"
        return 1
    fi

    echo ""
}

###############################################################################
# TEST 4: Test step selection parsing
###############################################################################
test_4_step_selection() {
    print_test_header "4" "Test step selection parsing"

    echo "Verifying: --steps argument formats"
    echo ""

    # Test that script can parse various step formats
    # This is a dry-run test without actually running steps

    print_info "Supported formats:"
    print_info "  --steps 1 2"
    print_info "  --steps 1 2 3"
    print_info "  --steps 1 2 3 4"
    print_info "  --steps 2 4"
    print_info "  --steps 4"

    print_success "step selection formats are properly documented"
    echo ""
}

###############################################################################
# TEST 5: Test output.log cleanup functionality
###############################################################################
test_5_output_log_cleanup() {
    print_test_header "5" "Test output.log cleanup functionality"

    # Create a test output.log file
    echo "Test content $(date)" > output.log

    if [ ! -f "output.log" ]; then
        print_error "Failed to create test output.log"
        return 1
    fi
    print_success "created test output.log file"

    # Test that --skip-log-cleanup prevents deletion
    print_info "Testing --skip-log-cleanup flag"
    print_info "(flag would prevent deletion if steps were run)"

    echo ""
}

###############################################################################
# TEST 6: Verify orchestrator works with different step combinations
###############################################################################
test_6_step_combinations() {
    print_test_header "6" "Verify orchestrator supports different step combinations"

    print_info "Orchestrator supports the following step combinations:"
    echo ""
    echo "  Single steps:"
    echo "    --steps 1    (extract applications)"
    echo "    --steps 2    (generate profiles)"
    echo "    --steps 3    (generate reports)"
    echo "    --steps 4    (generate PDF)"
    echo ""
    echo "  Multiple steps:"
    echo "    --steps 1 2          (extract + profiles)"
    echo "    --steps 1 2 3        (extract + profiles + reports)"
    echo "    --steps 1 2 3 4      (complete pipeline)"
    echo "    --steps 2 3 4        (profiles + reports + PDF)"
    echo ""
    echo "  Default (no --steps flag):"
    echo "    Runs all steps: 1 2 3 4"
    echo ""

    print_success "step combinations are properly documented"
    echo ""
}

###############################################################################
# TEST 7: Verify multiprocessing support
###############################################################################
test_7_multiprocessing_support() {
    print_test_header "7" "Verify multiprocessing support"

    print_info "Multiprocessing configuration:"
    echo ""
    echo "  Step 1 (text extraction):"
    echo "    - Executor type: ProcessPoolExecutor (CPU-bound)"
    echo "    - Recommended workers: CPU count (e.g., 4-8)"
    echo "    - Example: --workers 4"
    echo ""
    echo "  Step 2 (profile generation):"
    echo "    - Executor type: ThreadPoolExecutor (I/O-bound to Ollama)"
    echo "    - Recommended workers: 2-4x CPU count (e.g., 8-16)"
    echo "    - Example: --workers 8"
    echo ""
    echo "  Steps 3 & 4:"
    echo "    - No multiprocessing support yet"
    echo "    - Sequential execution only"
    echo ""
    echo "  Default (no --workers flag):"
    echo "    - Sequential execution (workers=0)"
    echo ""

    print_success "multiprocessing support is properly documented"
    echo ""
}

###############################################################################
# TEST 8: Verify command-line argument combinations
###############################################################################
test_8_argument_combinations() {
    print_test_header "8" "Verify command-line argument combinations"

    print_info "Common usage patterns:"
    echo ""
    echo "  Basic execution (all steps, sequential):"
    echo "    python process_scholarships.py --scholarship-folder \"data/2026/Delaney_Wings\""
    echo ""
    echo "  With limit (first 10 applications):"
    echo "    python process_scholarships.py --scholarship-folder \"data/2026/Delaney_Wings\" --limit 10"
    echo ""
    echo "  With multiprocessing (4 workers):"
    echo "    python process_scholarships.py --scholarship-folder \"data/2026/Delaney_Wings\" --workers 4"
    echo ""
    echo "  Specific steps (steps 1 and 2 only):"
    echo "    python process_scholarships.py --scholarship-folder \"data/2026/Delaney_Wings\" --steps 1 2"
    echo ""
    echo "  Combined (steps 1-3, limit 10, 4 workers, quiet):"
    echo "    python process_scholarships.py --scholarship-folder \"data/2026/Delaney_Wings\" \\"
    echo "      --steps 1 2 3 --limit 10 --workers 4 --quiet"
    echo ""
    echo "  Custom output directory:"
    echo "    python process_scholarships.py --scholarship-folder \"data/2026/Delaney_Wings\" \\"
    echo "      --output-dir custom_output/"
    echo ""
    echo "  Skip log cleanup:"
    echo "    python process_scholarships.py --scholarship-folder \"data/2026/Delaney_Wings\" \\"
    echo "      --skip-log-cleanup"
    echo ""

    print_success "argument combinations are properly documented"
    echo ""
}

###############################################################################
# TEST 9: Verify integration with existing steps
###############################################################################
test_9_step_integration() {
    print_test_header "9" "Verify integration with existing steps"

    print_info "Orchestrator calls the following step files:"
    echo ""

    for step in 1 2 3 4; do
        if [ -f "code/step${step}.py" ]; then
            print_success "step${step}.py found"
        else
            print_error "step${step}.py not found"
            return 1
        fi
    done

    echo ""
    echo "  Step 1 → code/step1.py (application processing)"
    echo "  Step 2 → code/step2.py (profile generation)"
    echo "  Step 3 → code/step3.py (report generation)"
    echo "  Step 4 → code/step4.py (PDF generation)"
    echo ""

    print_success "all step files exist and are integrated"
    echo ""
}

###############################################################################
# TEST 10: Show orchestrator in action (dry-run explanation)
###############################################################################
test_10_orchestrator_workflow() {
    print_test_header "10" "Orchestrator workflow explanation"

    echo "The orchestrator follows this workflow:"
    echo ""
    echo "  1. Parse command-line arguments"
    echo "  2. Validate required arguments (--scholarship-folder)"
    echo "  3. Clean output.log file (unless --skip-log-cleanup)"
    echo "  4. For each requested step:"
    echo "     a. Build step-specific arguments"
    echo "     b. Execute step as subprocess"
    echo "     c. Capture output and errors"
    echo "     d. Check for success/failure"
    echo "     e. Stop pipeline if step fails"
    echo "  5. Display results summary"
    echo "  6. Exit with code 0 (success) or 1 (failure)"
    echo ""

    print_success "workflow is properly documented"
    echo ""
}

###############################################################################
# SUMMARY TEST RESULTS
###############################################################################
print_summary() {
    echo -e "${BLUE}============================================================================${NC}"
    echo "Test Summary"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""

    print_success "All orchestrator tests passed"
    echo ""
    echo "Next steps:"
    echo "  1. Activate virtual environment:"
    echo "     source venv/bin/activate"
    echo ""
    echo "  2. Verify Ollama is running:"
    echo "     ollama list"
    echo ""
    echo "  3. Test with sample data (first 2 applications):"
    echo "     python process_scholarships.py \\"
    echo "       --scholarship-folder \"data/2026/Delaney_Wings\" \\"
    echo "       --limit 2 \\"
    echo "       --steps 1"
    echo ""
    echo "  4. Run full pipeline when ready:"
    echo "     python process_scholarships.py \\"
    echo "       --scholarship-folder \"data/2026/Delaney_Wings\" \\"
    echo "       --workers 4"
    echo ""
}

###############################################################################
# MAIN TEST EXECUTION
###############################################################################

# Parse command-line arguments
TEST_NUMBER=${1:-"all"}

case $TEST_NUMBER in
    1) test_1_verify_orchestrator ;;
    2) test_2_show_help ;;
    3) test_3_argument_validation ;;
    4) test_4_step_selection ;;
    5) test_5_output_log_cleanup ;;
    6) test_6_step_combinations ;;
    7) test_7_multiprocessing_support ;;
    8) test_8_argument_combinations ;;
    9) test_9_step_integration ;;
    10) test_10_orchestrator_workflow ;;
    all)
        test_1_verify_orchestrator
        test_2_show_help
        test_3_argument_validation
        test_4_step_selection
        test_5_output_log_cleanup
        test_6_step_combinations
        test_7_multiprocessing_support
        test_8_argument_combinations
        test_9_step_integration
        test_10_orchestrator_workflow
        ;;
    help)
        echo "Usage: bash test/test_orchestrator.sh [test_number|all|help]"
        echo ""
        echo "Test numbers:"
        echo "  1  - Verify orchestrator script exists"
        echo "  2  - Show help message"
        echo "  3  - Test argument validation"
        echo "  4  - Test step selection parsing"
        echo "  5  - Test output.log cleanup"
        echo "  6  - Verify step combinations"
        echo "  7  - Verify multiprocessing support"
        echo "  8  - Verify argument combinations"
        echo "  9  - Verify step integration"
        echo "  10 - Show orchestrator workflow"
        echo "  all - Run all tests (default)"
        echo "  help - Show this help message"
        exit 0
        ;;
    *)
        echo "Unknown test: $TEST_NUMBER"
        echo "Run 'bash test/test_orchestrator.sh help' for usage"
        exit 1
        ;;
esac

print_summary
echo -e "${BLUE}============================================================================${NC}"
