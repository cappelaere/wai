# Individual Example Files - Quick Start

All schema examples are now available as individual JSON files with a consistent naming convention.

## File Naming Convention

```
{agent_name}_agent_example_{number}.json
```

- `{agent_name}`: personal, academic, recommendation, social, application
- `{number}`: 1 (ideal/best case) or 2 (realistic/challenging case)

## Available Files

### Personal Agent
- `personal_agent_example_1.json` - Strong aviation-focused applicant (Sarah, 88/100)
- `personal_agent_example_2.json` - Career-changer (Michelle, 78/100)

### Academic Agent
- `academic_agent_example_1.json` - High performer (Jessica, 92/100)
- `academic_agent_example_2.json` - Non-traditional path (David, 78/100)

### Recommendation Agent
- `recommendation_agent_example_1.json` - Consensus endorsement (93/100)
- `recommendation_agent_example_2.json` - Mixed with growth areas (71/100)

### Social Agent
- `social_agent_example_1.json` - Strong presence (79/100)
- `social_agent_example_2.json` - Minimal presence (15/100)

### Application Agent
- `application_agent_example_1.json` - Complete application (95/100)
- `application_agent_example_2.json` - Partial application (62/100)

## Quick Load Examples

```python
import json

# Simple load
with open('schemas/personal_agent_example_1.json') as f:
    example = json.load(f)

# Use in prompt
prompt = f"""...
Here is an example of expected output:

{json.dumps(example, indent=2)}

..."""
```

## Integration Pattern

```python
class PersonalAgent(BaseAgent):
    def analyze_personal_profile(self, ...):
        # Load example
        with open('schemas/personal_agent_example_1.json') as f:
            example = json.load(f)
        
        example_text = json.dumps(example, indent=2)
        
        prompt = f"""[Task description]

Here is an example of expected output:

{example_text}

[Rest of prompt]"""
```

## Documentation

- **NAMING_CONVENTION.md** - Complete naming guide with best practices
- **INTEGRATION_GUIDE.md** - Step-by-step implementation instructions
- **EXAMPLES.md** - Full documentation and detailed descriptions

## Key Points

✓ All files are valid JSON
✓ All files follow their schema
✓ Example 1 shows ideal case (best for demos)
✓ Example 2 shows realistic case (best for testing)
✓ Files are organized by agent
✓ Easy to load programmatically
✓ Small file sizes (~2-3.5 KB each)

## Next Steps

1. Read NAMING_CONVENTION.md for the complete guide
2. Load examples in your agent code
3. Include examples in prompts
4. Test with integrated examples
5. Monitor improvements in JSON parsing quality

---

**Status**: Ready to integrate ✓
**Validation**: 10/10 examples valid ✓
**Total Size**: ~21 KB
