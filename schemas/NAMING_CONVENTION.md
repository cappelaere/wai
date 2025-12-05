# Schema Example Files - Naming Convention

This document explains the naming convention used for individual example files in the schemas directory.

## Naming Pattern

All example files follow this consistent pattern:

```
{agent_name}_agent_example_{number}.json
```

### Components

1. **{agent_name}**: The name of the agent (lowercase)
   - `personal` - PersonalAgent
   - `academic` - AcademicAgent
   - `recommendation` - RecommendationAgent
   - `social` - SocialAgent
   - `application` - ApplicationAgent

2. **_agent_** - Fixed separator indicating these are agent examples

3. **example_{number}** - Example identifier
   - `example_1` - First/ideal example (best case scenario)
   - `example_2` - Second/realistic example (real-world scenario)

4. **.json** - File extension

## File Listing

### Personal Agent Examples
```
personal_agent_example_1.json  - Strong aviation-focused applicant (Sarah, 88/100)
personal_agent_example_2.json  - Career-changer with emerging interest (Michelle, 78/100)
```

### Academic Agent Examples
```
academic_agent_example_1.json  - High-performing STEM student (Jessica, 92/100)
academic_agent_example_2.json  - Non-traditional path student (David, 78/100)
```

### Recommendation Agent Examples
```
recommendation_agent_example_1.json  - Strong consensus endorsement (93/100)
recommendation_agent_example_2.json  - Mixed with growth areas (71/100)
```

### Social Agent Examples
```
social_agent_example_1.json  - Strong professional presence (79/100)
social_agent_example_2.json  - Minimal presence (15/100)
```

### Application Agent Examples
```
application_agent_example_1.json  - Complete application (95/100)
application_agent_example_2.json  - Partial application (62/100)
```

## Usage in Code

### Loading Examples Programmatically

```python
from pathlib import Path
import json

def load_agent_example(agent_name, example_num):
    """Load an example for an agent.

    Args:
        agent_name: 'personal', 'academic', 'recommendation', 'social', 'application'
        example_num: 1 or 2

    Returns:
        Parsed JSON example dictionary
    """
    filename = f"{agent_name}_agent_example_{example_num}.json"
    schema_dir = Path(__file__).parent.parent.parent / "schemas"
    file_path = schema_dir / filename

    with open(file_path) as f:
        return json.load(f)

# Usage
example = load_agent_example('personal', 1)
```

### Using in Agent Prompts

```python
import json

class PersonalAgent(BaseAgent):
    # Load examples
    EXAMPLE_1 = load_agent_example('personal', 1)
    EXAMPLE_2 = load_agent_example('personal', 2)

    def analyze_personal_profile(self, ...):
        example_json = json.dumps(self.EXAMPLE_1, indent=2)

        prompt = f"""[Task description]

Here is an example of expected output:

{example_json}

[Rest of prompt]"""
```

## Directory Structure

```
schemas/
├── personal_agent_schema.json
├── personal_agent_example_1.json      ← Example file
├── personal_agent_example_2.json      ← Example file
│
├── academic_agent_schema.json
├── academic_agent_example_1.json      ← Example file
├── academic_agent_example_2.json      ← Example file
│
├── recommendation_agent_schema.json
├── recommendation_agent_example_1.json ← Example file
├── recommendation_agent_example_2.json ← Example file
│
├── social_agent_schema.json
├── social_agent_example_1.json        ← Example file
├── social_agent_example_2.json        ← Example file
│
├── application_agent_schema.json
├── application_agent_example_1.json   ← Example file
├── application_agent_example_2.json   ← Example file
│
└── [Documentation files]
    ├── EXAMPLES.md
    ├── INTEGRATION_GUIDE.md
    ├── NAMING_CONVENTION.md (this file)
    └── ...
```

## Example Numbers Convention

### Example 1: Best Case / Ideal Scenario
- Strong applicant with all positive indicators
- High scores (typically 85+)
- Demonstrates excellence and ideal profile
- Good for showing format and capabilities

**When to use:**
- Standard prompt examples
- Showing ideal output format
- Training and baseline comparison

### Example 2: Realistic / Challenging Scenario
- Real-world applicant with varied strengths
- Mixed or moderate scores (typically 70-85)
- Shows how to evaluate diverse applicants
- Demonstrates fairness and nuance

**When to use:**
- Edge case handling
- Showing realistic evaluations
- Testing fairness and objectivity
- Handling applicants with growth areas

## Integration Pattern

When integrating examples into agent code:

```python
# Step 1: Define constants with examples
class YourAgent(BaseAgent):
    EXAMPLE_1_PATH = "personal_agent_example_1.json"  # Best case
    EXAMPLE_2_PATH = "personal_agent_example_2.json"  # Realistic case

# Step 2: Load in prompts
def analyze_something(self):
    with open(self.EXAMPLE_1_PATH) as f:
        example = json.load(f)

    prompt = f"""
    [Your task]

    Here is an example of expected output:

    {json.dumps(example, indent=2)}

    [Rest of prompt]
    """
```

## File Size Guide

| File | Size | Time to Load |
|------|------|--------------|
| personal_agent_example_1.json | ~2 KB | <1 ms |
| personal_agent_example_2.json | ~2 KB | <1 ms |
| academic_agent_example_1.json | ~2 KB | <1 ms |
| academic_agent_example_2.json | ~2 KB | <1 ms |
| recommendation_agent_example_1.json | ~3 KB | <1 ms |
| recommendation_agent_example_2.json | ~2.5 KB | <1 ms |
| social_agent_example_1.json | ~1.5 KB | <1 ms |
| social_agent_example_2.json | ~1 KB | <1 ms |
| application_agent_example_1.json | ~2 KB | <1 ms |
| application_agent_example_2.json | ~2 KB | <1 ms |

**Total: ~21 KB across all 10 files**

## Best Practices

### Do's ✓
- Use consistent naming across agents
- Load examples from files (don't hardcode)
- Use example_1 for primary/ideal case
- Use example_2 for realistic/edge case
- Include both examples in comprehensive prompts
- Document which example you're using

### Don'ts ✗
- Don't modify example file contents
- Don't hardcode example JSON in code
- Don't use inconsistent naming
- Don't mix example numbers between agents
- Don't duplicate example content
- Don't create additional example files without updating this guide

## Validation

All example files have been validated:
- ✓ Valid JSON syntax
- ✓ Schema compliant
- ✓ All required fields present
- ✓ Appropriate score ranges
- ✓ Realistic content

To validate an example file:
```python
import json
from jsonschema import validate

# Load example and schema
with open('schemas/personal_agent_example_1.json') as f:
    example = json.load(f)

with open('schemas/personal_agent_schema.json') as f:
    schema = json.load(f)

# Validate
try:
    validate(instance=example, schema=schema)
    print("✓ Valid!")
except Exception as e:
    print(f"✗ Error: {e}")
```

## Migration from EXAMPLES.md

The large `EXAMPLES.md` file still exists and contains:
- Full documentation and descriptions
- Integration guidelines
- Discussion of example design choices
- Rationale and context

For implementation, use the individual `.json` files.
For learning and understanding, refer to `EXAMPLES.md`.

## Summary

| Item | Value |
|------|-------|
| Total Example Files | 10 |
| Agents Covered | 5 |
| Examples per Agent | 2 |
| Naming Pattern | `{agent}_agent_example_{n}.json` |
| Total Size | ~21 KB |
| Validation | 10/10 passed ✓ |

---

**Version:** 1.0
**Status:** Complete
**Last Updated:** November 16, 2024
