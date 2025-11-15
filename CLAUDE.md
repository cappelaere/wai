# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a WAI scholarship application processor that automates the analysis and evaluation of scholarship applications. It extracts information from application forms and attachments, then uses multiple AI agents (powered by Ollama) to generate detailed profiles and reports.

## Quick Start Commands

### Setup
```bash
# Create and activate virtual environment (Python 3.13)
python3.13 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r code/requirements.txt

# Verify Ollama is running
ollama list
```

### Running the Pipeline

#### Option 1: Using the Unified Orchestrator (Recommended)

The easiest way to run the complete pipeline with unified arguments:

```bash
source venv/bin/activate

# Run all steps (1, 2, 3, 4) with default settings
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings"

# Run with multiprocessing (4 workers for steps 1 & 2)
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --workers 4

# Run specific steps only (e.g., steps 1 and 2)
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" --steps 1 2

# Run with limit and custom options
python process_scholarships.py --scholarship-folder "data/2026/Delaney_Wings" \
  --limit 10 --workers 4 --steps 1 2 3 --quiet
```

**Key orchestrator features:**
- Single entry point for all steps
- Automatic output.log cleanup at start
- Unified arguments for all steps
- Selective step execution
- Error handling (stops at first failure)
- Progress tracking and timing

#### Option 2: Running Individual Steps (Advanced)

For more control, run each step separately:

```bash
source venv/bin/activate

# Step 1: Process applications and classify attachments
python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --limit 5 --workers 4

# Step 2: Generate profiles using AI agents (Application, Personal, Recommendation, Academic, Social)
python code/step2.py --scholarship-folder "Delaney_Wings" --workers 8

# Step 3: Generate review board reports
python code/step3.py --scholarship-folder "Delaney_Wings"

# Step 4: Combine reports and generate PDF
python code/step4.py --scholarship-folder "Delaney_Wings" --limit 10
```

### Running Tests
```bash
# Run individual test scripts from test/ directory
bash test/test_step1.sh
bash test/test_step2.sh
bash test/test_step3.sh
bash test/test_step4.sh
bash test/test_step5.sh
```

## Architecture

### Five-Step Pipeline

**Step 1: Application Processing**
- Input: Application folders in `data/{year}/{scholarship_name}/Applications/`
- Process: Extracts text from PDFs/documents using Docling, classifies attachments
- Output: `application_form_data.json`, `application_form_text.txt`, `attachments.json`, extracted text files
- Key classes: `ApplicationFileProcessor`, `DoclingTextExtractor`, `AttachmentClassifier`

**Step 2: Profile Generation**
- Input: Output from Step 1
- Process: Five specialized agents analyze the data
- Output: Five JSON profile files (see Agents section below)
- Key classes: `ApplicationAgent`, `PersonalAgent`, `RecommendationAgent`, `AcademicAgent`, `SocialAgent`

**Step 3: Report Generation**
- Input: Profile JSON files from Step 2
- Process: Generates markdown reports for review boards
- Output: Markdown files in `results/` directory

**Step 4: PDF Compilation**
- Input: Markdown reports from Step 3
- Process: Combines reports and generates PDF documents
- Output: PDF files

**Step 5: Statistics**
- Input: Profile data from Step 2
- Process: Aggregates and analyzes scholarship-wide statistics
- Output: Comprehensive statistics report

### Agent Architecture (Step 2)

Five specialized Ollama agents analyze different aspects of applications:

1. **ApplicationAgent**: Extracts structured application metadata (name, contact, demographics)
2. **PersonalAgent**: Analyzes essays/resumes for motivation, goals, leadership, character
3. **RecommendationAgent**: Processes recommendation letters for strengths and qualities
4. **AcademicAgent**: Extracts academic achievements and subject competencies from resumes
5. **SocialAgent**: Identifies social media presence (LinkedIn, Facebook, Instagram, TikTok)

Each agent uses Ollama locally to avoid API calls and costs. Model is configurable via `OLLAMA_MODEL` env var.

## Key Files and Modules

**Core Processing (`processor/`)**
- `processor/pipeline/`: Main pipeline scripts (step1.py to step5.py)
- `processor/agents/`: AI agents for analysis
  - `application_agent.py`: Application metadata extraction
  - `personal_agent.py`: Personal profile analysis
  - `recommendation_agent.py`: Recommendation letter analysis
  - `academic_agent.py`: Academic achievement extraction
  - `social_agent.py`: Social media identification
  - `base_agent.py`: Shared base class with Ollama integration
- `processor/utils/`: Shared utilities
  - `process_application.py`: File processing, text extraction, attachment classification
  - `processing_pool.py`: Multiprocessing support for parallelization
  - `logging_utils.py`: Centralized logging and execution tracking
  - `error_handling.py`: Unified error handling (ErrorResult, SuccessResult)
  - `generate_schemas.py`: Schema validation and generation
  - `generate_summary.py`: Summary report generation
- `processor/templates/`: Jinja2 templates for report generation

**Copilot Module (`copilot/`)** - New module for intelligent assistance
- `copilot/agents/`: Copilot-specific agents (ready for development)
- `copilot/tools/`: Tools and utilities for copilot operations
- `copilot/context/`: Session and context management

**Entry Points**
- `process_scholarships.py`: Unified orchestrator for running pipeline steps
- Individual steps can be run from `processor/pipeline/`

**Configuration**
- `.env`: Environment variables (Ollama model, host, paths)
- `.env.example`: Template for environment configuration

**Test Scripts (`test/`)**
- `test_orchestrator.sh`: Tests for the unified orchestrator
- Individual test scripts for each step with sample data

**Documentation**
- `ARCHITECTURE.md`: Detailed architecture and project structure
- `CLAUDE.md`: This file (guidance for Claude Code)

## Important Environment Variables

```
# Ollama Configuration
OLLAMA_MODEL=llama3.2:3b          # Local model to use
OLLAMA_HOST=http://localhost:11434 # Ollama server URL

# Paths
INPUT_DATA_DIR=data/2026           # Where scholarship folders are
OUTPUT_DATA_DIR=output/2026        # Where processed results go
```

See `.env.example` for all available options.

## Data Flow and Folder Structure

```
data/2026/                          # INPUT_DATA_DIR
├── Delaney_Wings/                  # Scholarship folder
│   ├── Applications/
│   │   ├── 12345/                  # Application folder
│   │   │   ├── 1_0.pdf             # Application form
│   │   │   ├── 1_1.pdf             # Attachment 1
│   │   │   └── 1_2.docx            # Attachment 2
│   │   └── 12346/
│   └── input/
│       └── personal_criteria.txt    # Custom evaluation criteria (optional)

output/2026/                         # OUTPUT_DATA_DIR (generated by step1.py)
├── Delaney_Wings/
│   ├── 12345/
│   │   ├── application_form_data.json
│   │   ├── application_form_text.txt
│   │   ├── attachments.json
│   │   ├── application_profile.json
│   │   ├── personal_profile.json
│   │   ├── recommendation_profile.json
│   │   ├── academic_profile.json
│   │   └── social_profile.json
│   └── 12346/
```

## Common Development Tasks

### Adding a New Agent Type
1. Create new agent class in `code/new_agent.py` inheriting agent patterns
2. Implement `analyze_*()` method following existing agent signatures
3. Add to Step 2 imports and execution loop in `step2.py`
4. Update this CLAUDE.md with new agent documentation

### Processing Pipeline Extension
- Each step outputs specific JSON files that the next step consumes
- To add intermediate processing, follow the pattern: create output JSON, update next step to read it
- All file paths use Pathlib (Path objects) for cross-platform compatibility

### Debugging Failed Applications
- Check `logs/` directory for execution logs
- Each application's output folder contains intermediate files
- Use `--limit N` in step scripts to process small batches for testing

## Dependencies

- **Python 3.13**: Runtime requirement
- **Ollama**: Local LLM inference (required for agent processing)
- **Docling**: Document parsing and text extraction (PDF, DOCX, images)
- **Pydantic**: Data validation and JSON serialization
- **Jinja2**: Report template rendering
- **Python-docx**: Word document processing
- **Pandas**: Data analysis and CSV/Excel handling
- **PyYAML**: Configuration files

See `code/requirements.txt` for complete dependency list with versions.

## Notes for Future Development

- Parallel processing is listed as a TODO (currently sequential per step)
- Code organization suggests future refactoring into "processor" folder
- Parser instantiation could be optimized (currently recreated per file)
- Statistics generation (Step 5) is the newest addition
- Personal criteria feature allows scholarship-specific evaluation rules
