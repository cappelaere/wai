# Usage Guide

This guide explains how to use the WAI scholarship application processor.

## Prerequisites

Before running the application processor, make sure you have:

1. **Python 3.13** installed
2. **Virtual environment** created and activated
3. **Dependencies** installed
4. **Ollama** set up and running (see `INSTALL_OLLAMA.md` or `code/OLLAMA_SETUP.md`)

## Quick Start

### 1. Activate Virtual Environment

**Always activate the virtual environment before running scripts:**

```bash
cd /Users/patrice/Development/scholarships
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### 2. Verify Setup

Check that everything is ready:

```bash
# Verify Python version
python --version  # Should show Python 3.13.0

# Verify Ollama is running
ollama list

# Check available models
ollama list
```

### 3. Run the Processor

The processing is divided into five steps that can be run together or separately.

**Step 1: Process Applications and Classify Attachments**

```bash
# Process all applications (default behavior)
python code/step1.py --scholarship-folder "data/2026/Delaney_Wings"

# Process first 5 applications only
python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --limit 5

# Process all applications (explicit)
python code/step1.py --scholarship-folder "data/2026/Delaney_Wings" --all
```

This will:
- Look for applications in `{scholarship_folder}/Applications/` subfolder
- Extract and analyze application forms
- Classify attachments (essay, resume, recommendation, medical certificate, flight log, etc.)
- Extract text from attachments and save to `.txt` files
- Skip empty or zero-byte files automatically
- Save results to `{OUTPUT_DATA_DIR}/{scholarship_folder_name}/{application_folder}/`

**Note:** By default, all application folders are processed. Use `--limit N` to process only the first N applications, or `--all` to explicitly process all (same as default).

**Step 2: Generate Profiles (All Agents)**

```bash
# Generate profiles for all processed applications
python code/step2.py --scholarship-folder "Delaney_Wings"
```

**Step 3: Generate Review Board Reports**

```bash
# Generate Markdown reports for all applications
python code/step3.py --scholarship-folder "Delaney_Wings"
```

**Step 4: Combine Reports and Generate PDF**

```bash
# Combine all reports and generate PDF
python code/step4.py --scholarship-folder "Delaney_Wings"

# Generate PDF for top 10 applicants by total score
python code/step4.py --scholarship-folder "Delaney_Wings" --limit 10
```

**Step 5: Generate Scholarship Statistics Report**

```bash
# Generate comprehensive statistics report for a scholarship
python code/step5.py --scholarship-folder "Delaney_Wings"
```

**For detailed usage instructions, see the sections below.**

## Command-Line Options

The Step 1 script (`code/step1.py`) supports the following options:

### Required/Optional Arguments

- `--scholarship-folder PATH`: Path to the scholarship folder (applications are in `Applications/` subfolder)
  - Default: Uses `SCHOLARSHIP_FOLDER` from `.env` file or environment variable
  - The script will look for applications in `{scholarship_folder}/Applications/`
  - Example: `--scholarship-folder "data/2026/Delaney_Wings"`

- `--application-folder NAME`: Process a specific application folder by name
  - Optional: If not specified, processes folders from the Applications subfolder
  - Example: `--application-folder "75179"`

- `--limit N`: Limit the number of application folders to process
  - Default: `0` (processes all folders by default)
  - Use `--limit N` to process only the first N folders
  - Example: `--limit 5` (processes first 5 folders only)

- `--all`: Process all application folders (overrides `--limit`)
  - Explicitly processes all applications (same as default when --limit is not specified)
  - Example: `--all`

- `--model MODEL_NAME`: Ollama model name to use
  - Default: Uses `OLLAMA_MODEL` from `.env` file or environment variable, or `llama3.2`
  - Example: `--model mistral` or `--model "llama3.2:3b"`

- `--output-dir PATH`: Base output directory for JSON profile files
  - Default: Uses `OUTPUT_DATA_DIR` from environment variable, or `output/`
  - Files are saved as: `{output-dir}/{scholarship_folder_name}/{application_folder}/application_profile.json`
  - Example: `--output-dir results/` (creates `results/Delaney_Wings/{app_folder}/application_profile.json`)

- `--quiet`: Suppress verbose output (only show errors and summary)
  - Useful for batch processing

- `--help`: Show help message with all options

**Step 2 script (`code/step2.py`) supports the following options:**

- `--output-dir PATH`: Base output directory containing Step 1 results
  - Default: `output/`
  - Example: `--output-dir output` or `--output-dir results/2026/`

- `--input-dir PATH`: Path to input folder containing `personal_criteria.txt`
  - Optional: If not specified, tries to find it relative to output directory
  - Example: `--input-dir "data/2026/Delaney_Wings/Wings_for_Val_Delaney_Applications/input"`

- `--application-folder NAME`: Process a specific application folder by name
  - Optional: If not specified, processes all folders with Step 1 results
  - Example: `--application-folder "101127"`

- `--limit N`: Limit the number of application folders to process
  - Useful for testing or processing a subset
  - Example: `--limit 5`

- `--model MODEL_NAME`: Ollama model name to use
  - Default: Uses `OLLAMA_MODEL` from `.env` file or environment variable, or `llama3.2`
  - Example: `--model mistral`

- `--quiet`: Suppress verbose output (only show errors and summary)

- `--help`: Show help message with all options

## Processing Steps

The application processing is divided into two steps:

### Step 1: Application Processing and Attachment Classification

Processes application forms, classifies attachments, and extracts text.

**What it does:**
1. Lists and identifies files in each application folder (skips empty or zero-byte files)
2. Identifies the application form (file without attachment index)
3. Validates that the application form is not empty
4. Extracts text from the application form using docling
5. Processes all attachments:
   - Skips empty or zero-byte files
   - Extracts text from each attachment
   - Saves extracted text to `.txt` files
   - Classifies each attachment (essay, resume, recommendation, medical certificate, flight log, etc.)
6. Saves all extracted data for Step 2 processing

**Output files:**
- `application_form_text.txt` - Extracted text from the application form
- `application_form_data.json` - Application form metadata and file list
- `attachments.json` - Detailed attachment classifications with extracted text file references
- `{attachment_name}.txt` - Extracted text from each attachment (if text was extracted)

**File structure:**
```
{OUTPUT_DATA_DIR}/
├── {scholarship_folder_name}/
│   ├── {application_folder_1}/
│   │   ├── application_form_text.txt
│   │   ├── application_form_data.json
│   │   ├── attachments.json
│   │   ├── {attachment_1}.txt
│   │   ├── {attachment_2}.txt
│   │   └── ...
│   ├── {application_folder_2}/
│   │   └── ...
│   └── ...
```

### Step 2: Profile Generation (All Agents)

Generates comprehensive profiles using multiple specialized agents (requires Step 1 to be completed first).

**What it does:**
1. Reads Step 1 results (application_form_data.json, application_form_text.txt, and attachments.json)
2. Loads additional criteria from `input/` folder if available:
   - `application_criteria.txt` - For ApplicationAgent
   - `personal_criteria.txt` - For PersonalAgent
   - `recommendation_criteria.txt` - For RecommendationAgent
   - `academic_criteria.txt` - For AcademicAgent
   - `social_criteria.txt` - For SocialAgent
3. Generates profiles using multiple agents:
   - **ApplicationAgent**: Analyzes application form completeness and quality
   - **PersonalAgent**: Analyzes essays and resumes for personal story and motivation
   - **RecommendationAgent**: Analyzes recommendation letters
   - **AcademicAgent**: Analyzes academic background and achievements
   - **SocialAgent**: Detects social media presence (LinkedIn, Facebook, Instagram, TikTok)
4. Calculates total score summary (sum of all overall scores)
5. Generates CSV spreadsheet with all applicant scores

**Output files:**
- `application_profile.json` - Complete profile with all agent results and total score summary
- `personal_profile.json` - Personal profile analysis
- `recommendation_profile.json` - Recommendation profile analysis
- `academic_profile.json` - Academic profile analysis
- `social_profile.json` - Social presence profile analysis

**Note:** You can run Step 2 separately after Step 1.

### Step 3: Generate Review Board Reports

Generates one-page Markdown reports for each application (requires Step 2 to be completed first).

**What it does:**
1. Reads `application_profile.json` files from Step 2 output
2. Extracts applicant information, scores, and summaries
3. Formats data using a customizable template
4. Generates individual Markdown reports for each application

**Output files:**
- `review_report.md` - One-page report for each application (in each application folder)
- `applicant_scores_summary.csv` - Spreadsheet with all applicants and scores (in OUTPUT_DATA_DIR/{scholarship_folder}/output/)

**Note:** Reports are generated in Markdown format and can be viewed in any Markdown viewer or converted to PDF. The CSV file is automatically generated after all reports are created.

### Step 4: Combine Reports and Generate PDF

Combines all review reports into a single document and generates a PDF (requires Step 3 to be completed first).

**What it does:**
1. Finds all `review_report.md` files from Step 3
2. Combines them into a single Markdown document
3. Converts the combined Markdown to HTML
4. Generates a PDF from the HTML
5. Saves both the combined Markdown and PDF files

**Output files:**
- `combined_review_reports.md` - Combined Markdown document (in OUTPUT_DATA_DIR/{scholarship_folder}/output/)
- `combined_review_reports.pdf` - Combined PDF document (in OUTPUT_DATA_DIR/{scholarship_folder}/output/)

**Command-line options:**
- `--scholarship-folder NAME`: Combine reports from a specific scholarship folder only
  - Example: `--scholarship-folder "Delaney_Wings"`
- `--output-dir PATH`: Base output directory containing Step 3 reports
  - Default: Uses `OUTPUT_DATA_DIR` from environment variable or `output/`
- `--output FILENAME`: Output PDF filename
  - Default: `combined_review_reports.pdf` in {scholarship_folder}/output/
- `--template PATH`: Path to custom report template file
  - Default: Uses built-in template from step3
- `--limit N`: Limit to top N applicants by total score
  - Default: `0` (process all applicants)
  - Example: `--limit 10` (processes top 10 applicants by total score)
  - Applications are sorted by total score (highest first) before applying the limit
- `--markdown-only`: Only generate combined markdown file, do not create PDF
- `--quiet`: Suppress verbose output (only show errors and summary)

**Note:** Requires `reportlab` library to be installed: `pip install reportlab`

### Step 5: Generate Scholarship Statistics Report

Generates a comprehensive statistics report for a particular scholarship (requires Step 2 to be completed first).

**What it does:**
1. Finds all `application_profile.json` files for the scholarship
2. Extracts statistics including:
   - Number of applicants
   - Score statistics (mean, median, min, max, percentiles)
   - Score distribution across ranges
   - Geographic distribution (countries and states/provinces)
   - Score breakdowns by agent (Application, Personal, Recommendation, Academic, Social)
   - Completeness metrics (resume, essay, recommendations, etc.)
   - Additional statistics (aviation path stages, social media presence, top cities)
3. Generates a markdown report using a template
4. Saves the report to the output directory

**Output files:**
- `statistics_report.md` - Statistics report in Markdown format (in OUTPUT_DATA_DIR/{scholarship_folder}/output/)

**Command-line options:**
- `--scholarship-folder NAME`: Scholarship folder name (required)
  - Example: `--scholarship-folder "Delaney_Wings"`
- `--output-dir PATH`: Base output directory containing application profiles
  - Default: Uses `OUTPUT_DATA_DIR` from environment variable or `output/`
- `--output FILENAME`: Output markdown filename
  - Default: `{scholarship_folder}_statistics_report.md` in output directory
- `--template PATH`: Path to custom statistics template file
  - Default: Uses built-in template from `code/templates/scholarship_statistics_template.md`
- `--quiet`: Suppress verbose output (only show errors and summary)

## Usage Examples

### Example 1: Process All Applications (Default Behavior)

```bash
source venv/bin/activate
# Processes all application folders (default)
python code/step1.py --scholarship-folder "data/2026/Delaney_Wings"
```

### Example 2: Process a Specific Application

```bash
source venv/bin/activate
python code/step1.py \
  --scholarship-folder "data/2026/Delaney_Wings" \
  --application-folder "75179"
```

### Example 3: Process Multiple Applications with Limit

```bash
source venv/bin/activate
python code/step1.py \
  --scholarship-folder "data/2026/Delaney_Wings" \
  --limit 5
```

### Example 4: Process All Applications

```bash
source venv/bin/activate
python code/step1.py \
  --scholarship-folder "data/2026/Delaney_Wings" \
  --all
```

### Example 5: Process with Custom Model

```bash
source venv/bin/activate
python code/step1.py \
  --scholarship-folder "data/2026/Delaney_Wings" \
  --limit 3 \
  --model mistral
```

### Example 6: Process and Save to Custom Output Directory

```bash
source venv/bin/activate
python code/step1.py \
  --scholarship-folder "data/2026/Delaney_Wings" \
  --limit 10 \
  --output-dir results/2026/
```

This will create files like: `results/2026/Delaney_Wings/75179/application_profile.json`

### Example 7: Run Step 2 Separately

```bash
source venv/bin/activate
# Generate profiles for all processed applications (default)
python code/step2.py --scholarship-folder "Delaney_Wings"

# Generate profiles for first 10 applications only
python code/step2.py --scholarship-folder "Delaney_Wings" --limit 10

# Generate profile for specific application
python code/step2.py --scholarship-folder "Delaney_Wings" --application-folder "75179"

# Use different model for profile generation
python code/step2.py --scholarship-folder "Delaney_Wings" --model mistral
```

### Example 8: Step 2 with Custom Input Directory

```bash
source venv/bin/activate
# Generate profiles for first 10 applications only
python code/step2.py \
  --scholarship-folder "Delaney_Wings" \
  --limit 10
```

### Example 9: Quiet Mode (Minimal Output)

```bash
source venv/bin/activate
# Step 1 with quiet mode
python code/step1.py \
  --scholarship-folder "data/2026/Delaney_Wings" \
  --limit 20 \
  --quiet

# Step 2 with quiet mode (first 20 applications only)
python code/step2.py --scholarship-folder "Delaney_Wings" --limit 20 --quiet
```

### Example 10: Using Environment Variables

If you have a `.env` file configured, you can omit some arguments:

```bash
source venv/bin/activate
# Uses SCHOLARSHIP_FOLDER and OLLAMA_MODEL from .env
python code/step1.py --limit 5
```

### Example 11: Generate Review Board Reports (Step 3)

```bash
source venv/bin/activate
# Generate reports for all applications
python code/step3.py

# Generate reports for a specific scholarship
python code/step3.py --scholarship-folder "Delaney_Wings"

# Generate reports for a specific application
python code/step3.py --scholarship-folder "Delaney_Wings" --application-folder "75179"

# Use a custom template
python code/step3.py --template "templates/custom_report.md"

# Generate reports for first 10 applications only
python code/step3.py --scholarship-folder "Delaney_Wings" --limit 10
```

### Example 12: Combine Reports and Generate PDF (Step 4)

```bash
source venv/bin/activate
# Combine all reports and generate PDF
python code/step4.py

# Combine reports for a specific scholarship
python code/step4.py --scholarship-folder "Delaney_Wings"

# Generate PDF for top 10 applicants by total score
python code/step4.py --scholarship-folder "Delaney_Wings" --limit 10

# Specify custom output filename
python code/step4.py --output "delaney_wings_reports.pdf"

# Generate only combined markdown (no PDF)
python code/step4.py --markdown-only
```

**Note:** Step 4 requires `reportlab` to be installed. If not installed, run:
```bash
pip install reportlab
```

### Example 13: Generate Scholarship Statistics Report (Step 5)

```bash
source venv/bin/activate
# Generate statistics report for a scholarship
python code/step5.py --scholarship-folder "Delaney_Wings"

# Generate report with custom output filename
python code/step5.py --scholarship-folder "Delaney_Wings" --output "delaney_statistics.md"

# Use custom template
python code/step5.py --scholarship-folder "Delaney_Wings" --template "templates/custom_stats.md"
```

## Personal Criteria File

You can define additional scholarship-specific criteria for the PersonalAgent by creating a `personal_criteria.txt` file in an `input` folder for your scholarship.

### File Location

Create the file at:
```
{scholarship_folder}/input/personal_criteria.txt
```

For example:
```
data/2026/Delaney_Wings/input/personal_criteria.txt
```

### File Format

The file should contain plain text describing the criteria you want the PersonalAgent to consider when analyzing applicants. For example:

```
# Personal Profile Evaluation Criteria

## Evaluation Focus Areas

1. **Aviation Passion and Commitment**
   - Look for evidence of long-term commitment to aviation
   - Consider participation in aviation-related activities, clubs, or organizations
   - Evaluate depth of understanding about aviation careers

2. **Leadership and Community Involvement**
   - Prioritize applicants with demonstrated leadership roles
   - Value community service, especially in aviation-related contexts
   - Consider involvement in WAI chapters or similar organizations

3. **Career Goals and Clarity**
   - Assess specificity and realism of career goals
   - Look for alignment between goals and scholarship purpose
   - Consider how well-defined the path to achieving goals is

## Scoring Guidelines

- Motivation scores should reflect both passion and demonstrated commitment
- Goals clarity should reward specific, well-thought-out plans
- Character/service/leadership should emphasize demonstrated actions over stated intentions
```

### Usage

The criteria file is automatically loaded when:
- Running Step 1 (looks in `{scholarship_folder}/input/personal_criteria.txt`)
- Running Step 2 (tries to find it relative to output directory, or use `--input-dir`)

If the file doesn't exist, processing continues normally without additional criteria.

## Environment Variables

You can configure the processor using a `.env` file (see `.env.example` for template):

### Available Variables

- `OLLAMA_MODEL`: Model name to use (default: `llama3.2:3b`)
  - Examples: `llama3.2:3b`, `mistral`, `phi3`, `llama3.2:1b`

- `OLLAMA_HOST`: Ollama server URL (default: `http://localhost:11434`)
  - Only needed if using a remote Ollama instance

- `OLLAMA_API_KEY`: Optional API key for remote Ollama instances

- `SCHOLARSHIP_FOLDER`: Default scholarship folder path (applications are in `Applications/` subfolder)
  - Example: `data/2026/Delaney_Wings`

- `APPLICATION_FOLDER`: Default application folder (for single processing)
  - Example: `75179`

- `INPUT_DATA_DIR`: Input data directory containing scholarship folders
  - Example: `data/2026`

- `OUTPUT_DATA_DIR`: Output data directory for processed results
  - Example: `output/2026`

- `LOG_OUTPUT_DIR`: Directory where execution logs are saved (default: `logs`)
  - Logs are appended to `{LOG_OUTPUT_DIR}/output.log`
  - Includes execution summaries, elapsed time, and exception details

- `SCHEMA_OUTPUT_DIR`: Directory where JSON schemas are stored (default: `schemas`)
  - Contains JSON Schema files for all agent outputs:
    - `application_agent_schema.json`
    - `personal_agent_schema.json`
    - `recommendation_agent_schema.json`
    - `academic_agent_schema.json`
    - `social_agent_schema.json`
  - Generate schemas with: `python code/generate_schemas.py`

### Example .env File

```bash
# Ollama Configuration
OLLAMA_MODEL=llama3.2:3b
OLLAMA_HOST=http://localhost:11434

# Application Processing Configuration
SCHOLARSHIP_FOLDER=data/2026/Delaney_Wings
APPLICATION_FOLDER=75179

# Data Directory Configuration
INPUT_DATA_DIR=data/2026
OUTPUT_DATA_DIR=output/2026

# Logging Configuration
LOG_OUTPUT_DIR=logs

# Schema Configuration
SCHEMA_OUTPUT_DIR=schemas
```

## Output

### Output File Structure

For each processed application, the following files are generated:

**Step 1 Output:**
- `application_form_text.txt` - Extracted text from the application form
- `application_form_data.json` - Application form metadata and file list
- `attachments.json` - Detailed attachment classifications with extracted text file references
- `{attachment_name}.txt` - Extracted text files (one per attachment with text)

**Step 2 Output:**
- `application_profile.json` - Application profile analysis (generated from Step 1 data)
- `personal_profile.json` - Personal profile analysis (if essays/resumes found)
- `recommendation_profile.json` - Recommendation profile analysis
- `academic_profile.json` - Academic profile analysis
- `social_profile.json` - Social presence profile analysis

**Output directory structure**: 
- Default: `{OUTPUT_DATA_DIR}/{scholarship_folder_name}/{application_folder}/`
- With custom `--output-dir`: `{output-dir}/{scholarship_folder_name}/{application_folder}/`
- The scholarship folder name (e.g., `Delaney_Wings`) is automatically included in the path

**Example output structure**:
```
output/2026/
├── Delaney_Wings/
│   ├── 75179/
│   │   ├── application_profile.json
│   │   ├── attachments.json
│   │   ├── application_form_text.txt
│   │   ├── application_form_data.json
│   │   ├── 75179_4_1.txt
│   │   ├── 75179_4_2.txt
│   │   └── ...
│   ├── 101127/
│   │   ├── application_profile.json
│   │   ├── attachments.json
│   │   ├── application_form_text.txt
│   │   ├── application_form_data.json
│   │   └── ...
│   └── ...
└── Evans_Wings/
    └── ...
```

### File Contents

**application_profile.json** contains:
- **Profile**: Extracted applicant information (name, contact, membership, etc.)
- **Summary**: Summary of the applicant and application
- **Score**: Completeness score (0-100) with breakdown and missing items
- **Attachments**: Summary of attachments found
- **Personal Profile**: Personal profile data (if Step 2 was run)

**attachments.json** contains:
- List of all attachments with classifications
- Each attachment includes: category, confidence, reasoning, filename, file extension, text file reference

**personal_profile.json** contains:
- **Summary**: 1 paragraph summary of the applicant's personal story
- **Profile Features**: Motivation, career goals, aviation path stage, community service, leadership roles, character indicators
- **Scores**: Motivation, goals clarity, character/service/leadership, and overall personal profile scores (0-100)
- **Score Breakdown**: Reasoning for each score

### Console Output

**Step 1** provides detailed progress information:

1. **File listing**: Shows all files found in the application folder
2. **Application form identification**: Identifies the main application form
3. **Text extraction**: Shows extraction progress (text length only in verbose mode)
4. **Application analysis**: Shows model being used and analysis progress
5. **Attachment processing**: Shows progress for each attachment (classification and text extraction)
6. **Personal profile generation**: Shows if essays/resumes found and profile generation progress
7. **Results**: Displays the generated profile JSON (in verbose mode)
8. **Summary**: Final summary with success/failure counts

**Step 2** provides:

1. **Loading Step 1 results**: Shows which files are being loaded
2. **Personal profile generation**: Shows essays/resumes found and generation progress
3. **Results**: Shows where files are saved
4. **Summary**: Final summary with success/failure counts

### Processing Summary

At the end, you'll see a summary like:

```
============================================================
Processing Summary
============================================================
Total processed: 5
Successful: 4
Failed: 1

Failed applications:
  - 12345: ERROR: No application form found
============================================================
```

## Troubleshooting

### Error: "Cannot connect to Ollama"

**Solution**: Make sure Ollama is running:

```bash
# Check if Ollama is running
ollama list

# If not running, start it
ollama serve
```

### Error: "Model not found"

**Solution**: Download the model first:

```bash
ollama pull llama3.2:3b
# or
ollama pull mistral
```

### Error: "No application form found"

**Solution**: Check that the application folder contains files matching the expected naming pattern:
- Format: `{membership_number}_{application_number}.{ext}` or `{membership_number}_{application_number}_{attachment_index}.{ext}`
- Supported formats: PDF, DOCX, PNG, JPG, JPEG
- Note: Empty or zero-byte files are automatically skipped

### Error: "Application form is empty (zero bytes)"

**Solution**: The application form file exists but is empty. This could indicate:
- File corruption
- Incomplete file upload
- File system issue

Check the file manually and replace it if necessary. Empty files are automatically skipped during processing.

### Error: "Folder does not exist"

**Solution**: Verify the path is correct:

```bash
# Check if the scholarship folder exists
ls -la "data/2026/Delaney_Wings"

# Check if Applications subfolder exists
ls -la "data/2026/Delaney_Wings/Applications"

# Use absolute path if needed
python code/step1.py --scholarship-folder "/full/path/to/scholarship_folder" --limit 1
```

**Note:** The script looks for applications in `{scholarship_folder}/Applications/`. If the `Applications` subfolder doesn't exist, it will use the scholarship folder directly (with a warning).

### Error: Import errors

**Solution**: Make sure virtual environment is activated and dependencies are installed:

```bash
source venv/bin/activate
pip install -r code/requirements.txt
```

### Performance Tips

1. **Use smaller models for faster processing**: `llama3.2:1b` or `llama3.2:3b`
2. **Use `--limit` for testing**: Test with a small number first
3. **Use `--quiet` for batch processing**: Reduces console output
4. **Process in batches**: Use `--limit` to process manageable chunks

## Getting Help

For more information:

```bash
source venv/bin/activate
python code/step1.py --help
```

This will display all available options with descriptions and examples.

## Next Steps

After processing applications:

1. Review the generated JSON profile files
2. Check the completeness scores to identify incomplete applications
3. Use the extracted profiles for further analysis or reporting
4. Process additional applications as needed

