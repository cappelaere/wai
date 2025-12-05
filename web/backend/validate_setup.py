#!/usr/bin/env python3
"""
Validate Scholarship Copilot Setup
Checks all required dependencies and configurations
"""

import sys
import os
from pathlib import Path
from typing import Tuple, List

def print_header(message: str):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"  {message}")
    print(f"{'='*60}")

def print_check(name: str, passed: bool, message: str = ""):
    """Print a check result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status:8} | {name:40} | {message}")

def check_python_version() -> bool:
    """Check Python version is 3.13+"""
    version = sys.version_info
    required = (3, 13)
    passed = version >= required
    print_check(
        "Python Version",
        passed,
        f"{version.major}.{version.minor}.{version.micro} (need 3.13+)"
    )
    return passed

def check_dependencies() -> Tuple[bool, List[str]]:
    """Check required packages are installed"""
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'anthropic': 'Anthropic SDK',
        'sqlalchemy': 'SQLAlchemy',
    }

    all_passed = True
    missing = []

    for package, name in required_packages.items():
        try:
            __import__(package)
            print_check(f"Package: {name}", True)
        except ImportError:
            print_check(f"Package: {name}", False, "Not installed")
            all_passed = False
            missing.append(package)

    return all_passed, missing

def check_file_structure() -> bool:
    """Check required files exist"""
    base_path = Path(__file__).parent
    required_files = [
        'app/__init__.py',
        'app/main.py',
        'app/config.py',
        'app/mcp/client.py',
        'app/mcp/servers/base.py',
        'app/mcp/servers/application_data.py',
        'app/mcp/servers/analysis.py',
        'app/mcp/servers/context.py',
        'app/mcp/servers/processor.py',
        'app/mcp/tools/registry.py',
        'app/mcp/tools/schemas.py',
        'app/copilot/agent.py',
        'app/services/claude_client.py',
        'app/services/session_manager.py',
        'app/api/routes.py',
        'app/models/schemas.py',
        'requirements.txt',
    ]

    all_passed = True
    for file_path in required_files:
        full_path = base_path / file_path
        exists = full_path.exists()
        print_check(f"File: {file_path}", exists)
        if not exists:
            all_passed = False

    return all_passed

def check_env_file() -> bool:
    """Check .env file exists and has API key"""
    env_file = Path(__file__).parent / '.env'

    exists = env_file.exists()
    print_check("File: .env", exists, "Configuration file")

    if exists:
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                has_api_key = 'ANTHROPIC_API_KEY' in content
                has_value = 'sk-ant-' in content or 'YOUR_KEY' in content

                if has_api_key and has_value:
                    print_check("  └─ ANTHROPIC_API_KEY", True, "Found")
                elif has_api_key:
                    print_check("  └─ ANTHROPIC_API_KEY", False, "Not configured (placeholder)")
                else:
                    print_check("  └─ ANTHROPIC_API_KEY", False, "Missing")

                return has_api_key and has_value
        except Exception as e:
            print_check("  └─ Read .env", False, str(e))
            return False
    else:
        print_check("  └─ API key configured", False, "Create .env file first")
        return False

def check_processor_data() -> bool:
    """Check if processor output directory exists"""
    output_path = Path(__file__).parent.parent.parent / 'output'
    exists = output_path.exists()

    print_check(
        "Processor Data",
        exists,
        f"{output_path if exists else 'Not found - run process_scholarships.py first'}"
    )

    if exists:
        # Count files
        json_files = list(output_path.glob('**/*.json'))
        print(f"         | Found {len(json_files)} JSON files")

    return exists

def check_frontend_files() -> bool:
    """Check frontend files exist"""
    frontend_path = Path(__file__).parent.parent / 'frontend'
    required_files = [
        'index.html',
        'app.js',
        'style.css',
    ]

    all_passed = True
    for file_name in required_files:
        file_path = frontend_path / file_name
        exists = file_path.exists()
        print_check(f"Frontend: {file_name}", exists)
        if not exists:
            all_passed = False

    return all_passed

def check_imports() -> bool:
    """Check if main modules can be imported"""
    try:
        sys.path.insert(0, str(Path(__file__).parent))

        # Try importing key modules
        modules = [
            ('app.config', 'Configuration'),
            ('app.mcp.tools.registry', 'Tool Registry'),
            ('app.services.session_manager', 'Session Manager'),
            ('app.models.schemas', 'Schemas'),
        ]

        all_passed = True
        for module_name, display_name in modules:
            try:
                __import__(module_name)
                print_check(f"Import: {display_name}", True)
            except Exception as e:
                print_check(f"Import: {display_name}", False, str(e)[:40])
                all_passed = False

        return all_passed
    except Exception as e:
        print_check("Import test", False, str(e))
        return False

def main():
    """Run all validation checks"""
    print_header("SCHOLARSHIP COPILOT SETUP VALIDATION")

    results = []

    # System checks
    print_header("System Requirements")
    results.append(("Python Version", check_python_version()))

    # Dependencies
    print_header("Dependencies")
    deps_ok, missing = check_dependencies()
    results.append(("Dependencies", deps_ok))
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Install with: pip install -r requirements.txt\n")

    # File structure
    print_header("File Structure")
    results.append(("File Structure", check_file_structure()))

    # Configuration
    print_header("Configuration")
    results.append(("Environment File", check_env_file()))

    # Data
    print_header("Data & Processor")
    results.append(("Processor Data", check_processor_data()))

    # Frontend
    print_header("Frontend Files")
    results.append(("Frontend Files", check_frontend_files()))

    # Imports
    print_header("Module Imports")
    results.append(("Module Imports", check_imports()))

    # Summary
    print_header("VALIDATION SUMMARY")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")

    print(f"\nResult: {passed}/{total} checks passed")

    if passed == total:
        print("\n✓ All checks passed! Ready to start:")
        print("  1. cd web/backend")
        print("  2. source venv/bin/activate")
        print("  3. python run.py")
        return 0
    else:
        print("\n✗ Some checks failed. Please review above.")
        if not deps_ok:
            print("  Install dependencies: pip install -r requirements.txt")
        return 1

if __name__ == '__main__':
    sys.exit(main())
