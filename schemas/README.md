# Agent Output Schemas

This directory contains JSON Schema files that define the structure of output data from all agents used in the scholarship application processing pipeline.

## Schema Files

- **application_agent_schema.json** - Schema for ApplicationAgent output
  - Defines the structure of `application_profile.json`
  - Includes profile information, scores, and completeness metrics

- **personal_agent_schema.json** - Schema for PersonalAgent output
  - Defines the structure of `personal_profile.json`
  - Includes personal summary, motivation, career goals, and character indicators

- **recommendation_agent_schema.json** - Schema for RecommendationAgent output
  - Defines the structure of `recommendation_profile.json`
  - Includes recommendation letter analysis and aggregate scores

- **academic_agent_schema.json** - Schema for AcademicAgent output
  - Defines the structure of `academic_profile.json`
  - Includes academic performance, relevance, and readiness scores

- **social_agent_schema.json** - Schema for SocialAgent output
  - Defines the structure of `social_profile.json`
  - Includes social media platform presence and professional presence scores

## Regenerating Schemas

To regenerate all schemas:

```bash
python code/generate_schemas.py
```

This will update all schema files in the `schemas/` directory (or the directory specified by `SCHEMA_OUTPUT_DIR` environment variable).

## Schema Location

By default, schemas are stored in the `schemas/` directory. You can customize this by setting the `SCHEMA_OUTPUT_DIR` environment variable in your `.env` file:

```bash
SCHEMA_OUTPUT_DIR=schemas
```

## Usage

These schemas can be used for:
- Validating agent output data
- Documenting expected data structures
- Generating TypeScript types or other language bindings
- API documentation
- Data quality checks

