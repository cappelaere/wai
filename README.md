# Scholarships Project

This project requires Python 3.13 and a virtual environment for dependency management.

## Prerequisites

- macOS (tested on macOS 12+)
- Administrator access (for Python installation)

## Installation

### Step 1: Install Python 3.13

#### Option A: Using Homebrew (Recommended)

If you have Homebrew installed and it's working properly:

```bash
brew install python@3.13
```

#### Option B: Using Official Python Installer

1. Download the Python 3.13 installer from [python.org](https://www.python.org/downloads/)
2. Run the installer package (`.pkg` file)
3. Follow the installation wizard
4. Verify installation:

```bash
python3.13 --version
```

You should see: `Python 3.13.0` (or similar)

### Step 2: Create Virtual Environment

Navigate to the project directory and create a virtual environment:

```bash
cd /Users/patrice/Development/scholarships
python3.13 -m venv venv
```

This creates a virtual environment in the `venv` directory.

### Step 3: Activate Virtual Environment

**On macOS/Linux:**

```bash
source venv/bin/activate
```

When activated, your terminal prompt will show `(venv)` at the beginning.

### Step 4: Install Dependencies

With the virtual environment activated, install the project dependencies:

```bash
pip install --upgrade pip
pip install -r code/requirements.txt
```

This will install all required packages listed in `code/requirements.txt`.

## Usage

### Activating the Virtual Environment

Each time you work on this project, activate the virtual environment:

```bash
source venv/bin/activate
```

### Deactivating the Virtual Environment

When you're done working, deactivate the virtual environment:

```bash
deactivate
```

### Running the Application Processor

#### Option 1: Using the Unified Orchestrator (Recommended)

The easiest way to run the complete pipeline (all steps) with unified arguments:

```bash
# Always activate virtual environment first
source venv/bin/activate

# Run all steps (1, 2, 3, 4) with default settings
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings"

# Run with multiprocessing for better performance
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --workers 4

# Run specific steps only
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --steps 1 2

# Run with limit (for testing)
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --limit 5
```

#### Option 2: Running Individual Steps

For more control, you can run each step separately:

```bash
# Always activate virtual environment first
source venv/bin/activate

# Step 1: Process first 5 applications (for testing)
python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --limit 5

# Step 2: Generate profiles for all applications
python code/step2.py --scholarship-folder "Delaney_Wings"

# Step 3: Generate reports
python code/step3.py --scholarship-folder "Delaney_Wings"

# Step 4: Generate PDF
python code/step4.py --scholarship-folder "Delaney_Wings"
```

**For detailed usage instructions, see [CLAUDE.md](CLAUDE.md)**

### Verifying Python Version

To confirm you're using Python 3.13 in the virtual environment:

```bash
python --version
```

You should see: `Python 3.13.0`

### Checking Virtual Environment Location

To see which Python interpreter is being used:

```bash
which python
```

This should point to: `/Users/patrice/Development/scholarships/venv/bin/python`

## Project Structure

```
scholarships/
├── code/
│   ├── docs/                    # Project documentation
│   ├── step1.py                 # Step 1: Application processing script
│   ├── step2.py                 # Step 2: Personal profile generation script
│   ├── process_application.py   # Processing classes and utilities
│   ├── requirements.txt         # Python dependencies
│   └── setup_ollama.sh          # Ollama setup script
├── data/                        # Data files and application materials
│   └── 2026/                   # Year-specific data
├── .env                         # Environment variables (not in git)
├── .env.example                 # Environment variables template
└── venv/                       # Virtual environment (created by setup)
```

## Troubleshooting

### Python 3.13 Not Found

If `python3.13` command is not found:

1. Verify Python 3.13 is installed:
   ```bash
   ls /usr/local/bin/python3.13
   ```

2. If not found, reinstall using one of the methods above.

### Virtual Environment Issues

If you encounter issues with the virtual environment:

1. Delete the existing virtual environment:
   ```bash
   rm -rf venv
   ```

2. Recreate it:
   ```bash
   python3.13 -m venv venv
   ```

3. Activate and reinstall dependencies:
   ```bash
   source venv/bin/activate
   pip install -r code/requirements.txt
   ```

### Permission Errors

If you encounter permission errors during installation:

- Make sure you have administrator access
- Try using `sudo` for system-wide Python installation (not recommended for virtual environments)
- Virtual environments should be created without `sudo`

## Notes

- The virtual environment (`venv/`) should be added to `.gitignore` if using version control
- Always activate the virtual environment before running project scripts
- Keep `requirements.txt` updated when adding new dependencies

## Additional Resources

- [Python 3.13 Documentation](https://docs.python.org/3.13/)
- [Python Virtual Environments Guide](https://docs.python.org/3/tutorial/venv.html)
- [pip Documentation](https://pip.pypa.io/)

