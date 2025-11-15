# Project Architecture

This document describes the reorganized project structure for better separation of concerns and to support the new copilot module.

## Overview

```
scholarships/
├── processor/              # Main processing pipeline
│   ├── pipeline/          # Processing steps (step1-5)
│   ├── agents/            # AI agents for analysis
│   ├── utils/             # Shared utilities
│   └── templates/         # Report templates
│
├── copilot/               # Copilot assistant module (new)
│   ├── agents/            # Copilot-specific agents
│   ├── tools/             # Copilot tools and utilities
│   └── context/           # Session and context management
│
├── code/                  # Legacy code directory (for reference)
├── data/                  # Input data
├── output/                # Processing output
├── test/                  # Test scripts
└── results/               # Results and reports
```

## Processor Module

The processor handles the main scholarship processing pipeline:

### Pipeline (processor/pipeline/)
- **step1.py**: Application processing and attachment classification
- **step2.py**: Profile generation using AI agents
- **step3.py**: Report generation
- **step4.py**: PDF compilation
- **step5.py**: Statistics generation

### Agents (processor/agents/)
Specialized AI agents for different aspects of analysis:
- **ApplicationAgent**: Extracts application metadata
- **PersonalAgent**: Analyzes personal essays and motivation
- **RecommendationAgent**: Processes recommendation letters
- **AcademicAgent**: Extracts academic achievements
- **SocialAgent**: Identifies social media presence
- **BaseAgent**: Shared base class with Ollama integration

### Utils (processor/utils/)
Shared utilities and helpers:
- **process_application.py**: File processing and text extraction
- **processing_pool.py**: Multiprocessing support
- **logging_utils.py**: Centralized logging
- **error_handling.py**: Unified error handling
- **generate_schemas.py**: JSON schema validation
- **generate_summary.py**: Summary report generation

### Templates (processor/templates/)
Jinja2 templates for report generation

## Copilot Module

The copilot provides intelligent assistance and automation (new module, ready for development):

### Agents (copilot/agents/)
AI agents for user assistance and guidance

### Tools (copilot/tools/)
Tools for:
- Integration with processor pipeline
- File operations
- Data transformation
- User assistance

### Context (copilot/context/)
Session and state management for user interactions

## Entry Points

### Orchestrator
- **process_scholarships.py**: Unified entry point for running pipeline steps

### Direct Step Execution
Steps can be run individually:
```bash
python processor/pipeline/step1.py --scholarship-folder "data/2026/Delaney_Wings"
```

### Copilot (Future)
Will provide interactive assistance for users

## Module Imports

### From Processor
```python
from processor.agents.application_agent import ApplicationAgent
from processor.utils.process_application import ApplicationFileProcessor
from processor.pipeline.step1 import process_application_step1
```

### From Copilot (Future)
```python
from copilot.agents import CopilotAgent
from copilot.tools import CopilotTools
from copilot.context import SessionContext
```

## Key Design Decisions

1. **Separated Concerns**: Processor handles data processing, copilot handles user assistance
2. **Package Structure**: Each module is a proper Python package with `__init__.py` files
3. **Relative Imports**: All internal imports use absolute imports from package roots
4. **Backward Compatibility**: Legacy code/requirements.txt maintained for reference
5. **Multiprocessing Support**: ProcessingPool abstraction for flexible parallelization

## Migration Notes

- Original code/ directory files have been moved to processor/ folder structure
- All imports updated to use new package paths
- process_scholarships.py remains at project root as the main entry point
- Test scripts updated to reference new locations
- Virtual environment requirements remain the same

## Future Development

The new structure supports:
- Adding copilot features without cluttering processor
- Better code organization and maintainability
- Easier testing and isolation of components
- Clear separation between data processing and user assistance

See copilot/README.md for copilot-specific documentation.
